// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title ATCBridge
 * @dev ATC-5000 Cross-Chain Bridge — Lock-Mint Mechanismus
 * Lock ATC auf A-TownChain → Mint wATC auf Ethereum/Solana
 * Relayer: 3-of-5 Multi-Sig
 * Max TX: 1.000.000 ATC
 * Daily Limit: 5.000.000 ATC
 * Timelock: 24h für TX > 100.000 ATC
 */
contract ATCBridge is Ownable, ReentrancyGuard, Pausable {

    // ── Konstanten ────────────────────────────────────────
    uint256 public constant MAX_TX_AMOUNT     = 1_000_000 ether;
    uint256 public constant DAILY_LIMIT       = 5_000_000 ether;
    uint256 public constant TIMELOCK_THRESHOLD=   100_000 ether;
    uint256 public constant TIMELOCK_DELAY    = 24 hours;
    uint256 public constant RELAYER_THRESHOLD = 3;   // 3-of-5 Signaturen

    // ── State ─────────────────────────────────────────────
    IERC20  public atcToken;
    uint256 private _bridgeTxCount;

    // Tägl. Limit-Tracking
    uint256 public  dailyVolume;
    uint256 public  lastDayReset;

    // Relayer-Set
    mapping(address => bool) public isRelayer;
    uint256 public relayerCount;

    enum TxStatus { Pending, Locked, Released, Timelocked, Cancelled }

    struct BridgeTx {
        uint256   txId;
        address   sender;
        uint256   amount;
        string    destinationChain;   // "ethereum" | "solana"
        string    destinationAddress;
        uint256   lockedAt;
        uint256   executeAfter;       // für Timelock
        TxStatus  status;
        bytes32   txHash;             // Cross-Chain TX Hash (nach Release)
    }

    mapping(uint256 => BridgeTx)                          public bridgeTxs;
    mapping(uint256 => mapping(address => bool))          public relayerSigned;
    mapping(uint256 => uint256)                           public signatureCount;
    mapping(bytes32 => bool)                              public processedHashes; // Replay-Schutz

    // ── Events ────────────────────────────────────────────
    event ATCLocked(uint256 indexed txId, address indexed sender,
                    uint256 amount, string destChain, string destAddress);
    event ATCReleased(uint256 indexed txId, address indexed recipient,
                      uint256 amount, bytes32 crossChainHash);
    event RelayerSigned(uint256 indexed txId, address indexed relayer,
                        uint256 sigCount);
    event BridgePaused(address by);
    event RelayerAdded(address relayer);
    event RelayerRemoved(address relayer);

    // ── Konstruktor ───────────────────────────────────────
    constructor(address _atcToken, address[] memory _relayers)
        Ownable(msg.sender)
    {
        require(_relayers.length == 5, "Need exactly 5 relayers");
        atcToken     = IERC20(_atcToken);
        lastDayReset = block.timestamp;
        for (uint256 i = 0; i < _relayers.length; i++) {
            isRelayer[_relayers[i]] = true;
        }
        relayerCount = 5;
    }

    // ── ATC sperren (→ Cross-Chain) ───────────────────────
    function lockATC(
        uint256 amount,
        string  memory destinationChain,
        string  memory destinationAddress
    ) external nonReentrant whenNotPaused returns (uint256)
    {
        require(amount > 0 && amount <= MAX_TX_AMOUNT, "Invalid amount");
        _resetDailyIfNeeded();
        require(dailyVolume + amount <= DAILY_LIMIT, "Daily limit exceeded");

        require(
            atcToken.transferFrom(msg.sender, address(this), amount),
            "Transfer failed"
        );

        uint256 txId = _bridgeTxCount++;
        uint256 executeAfter = (amount >= TIMELOCK_THRESHOLD)
            ? block.timestamp + TIMELOCK_DELAY
            : block.timestamp;

        bridgeTxs[txId] = BridgeTx({
            txId:               txId,
            sender:             msg.sender,
            amount:             amount,
            destinationChain:   destinationChain,
            destinationAddress: destinationAddress,
            lockedAt:           block.timestamp,
            executeAfter:       executeAfter,
            status:             TxStatus.Locked,
            txHash:             bytes32(0)
        });

        dailyVolume += amount;
        emit ATCLocked(txId, msg.sender, amount, destinationChain, destinationAddress);
        return txId;
    }

    // ── ATC freigeben (Relayer-Signatur) ──────────────────
    function signRelease(uint256 bridgeTxId) external {
        require(isRelayer[msg.sender], "Not a relayer");
        BridgeTx storage tx_ = bridgeTxs[bridgeTxId];
        require(tx_.status == TxStatus.Locked, "Not locked");
        require(!relayerSigned[bridgeTxId][msg.sender], "Already signed");

        relayerSigned[bridgeTxId][msg.sender] = true;
        signatureCount[bridgeTxId]++;

        emit RelayerSigned(bridgeTxId, msg.sender, signatureCount[bridgeTxId]);
    }

    // ── Release ausführen (nach Threshold + Timelock) ─────
    function executeRelease(
        uint256 bridgeTxId,
        address recipient,
        bytes32 crossChainHash
    ) external nonReentrant whenNotPaused {
        require(isRelayer[msg.sender], "Not a relayer");
        BridgeTx storage tx_ = bridgeTxs[bridgeTxId];
        require(tx_.status == TxStatus.Locked, "Not locked");
        require(signatureCount[bridgeTxId] >= RELAYER_THRESHOLD, "Not enough signatures");
        require(block.timestamp >= tx_.executeAfter, "Timelock active");
        require(!processedHashes[crossChainHash], "Already processed");

        processedHashes[crossChainHash] = true;
        tx_.status  = TxStatus.Released;
        tx_.txHash  = crossChainHash;

        atcToken.transfer(recipient, tx_.amount);
        emit ATCReleased(bridgeTxId, recipient, tx_.amount, crossChainHash);
    }

    // ── Emergency Cancel ──────────────────────────────────
    function cancelBridgeTx(uint256 bridgeTxId) external onlyOwner {
        BridgeTx storage tx_ = bridgeTxs[bridgeTxId];
        require(tx_.status == TxStatus.Locked, "Not locked");
        tx_.status = TxStatus.Cancelled;
        atcToken.transfer(tx_.sender, tx_.amount);
    }

    // ── Relayer-Management ────────────────────────────────
    function addRelayer(address relayer) external onlyOwner {
        require(!isRelayer[relayer], "Already relayer");
        isRelayer[relayer] = true;
        relayerCount++;
        emit RelayerAdded(relayer);
    }

    function removeRelayer(address relayer) external onlyOwner {
        require(isRelayer[relayer], "Not a relayer");
        require(relayerCount > RELAYER_THRESHOLD, "Too few relayers");
        isRelayer[relayer] = false;
        relayerCount--;
        emit RelayerRemoved(relayer);
    }

    // ── Pause ─────────────────────────────────────────────
    function emergencyPause() external onlyOwner {
        _pause();
        emit BridgePaused(msg.sender);
    }
    function unpause() external onlyOwner { _unpause(); }

    // ── Hilfsfunktionen ───────────────────────────────────
    function _resetDailyIfNeeded() internal {
        if (block.timestamp >= lastDayReset + 1 days) {
            dailyVolume  = 0;
            lastDayReset = block.timestamp;
        }
    }

    function getBridgeTx(uint256 txId) external view returns (BridgeTx memory) {
        return bridgeTxs[txId];
    }

    function getStats() external view returns (
        uint256 total, uint256 lockedATC, uint256 dailyVol
    ) {
        total    = _bridgeTxCount;
        lockedATC= atcToken.balanceOf(address(this));
        dailyVol = dailyVolume;
    }
}
