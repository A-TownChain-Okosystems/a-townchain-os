// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title GenesisToken
 * @dev ATC-001 Genesis Token — einmaliger, nicht transferierbarer Ursprungs-Token
 * Menge: genau 1
 * Nicht transferierbar — symbolischer Ursprungs-Token
 * Gesperrt nach Initialisierung
 */
contract GenesisToken is Ownable {

    // ── State ─────────────────────────────────────────────
    string  public constant TOKEN_ID   = "ATC-001-GENESIS";
    string  public constant NAME       = "A-TownChain Genesis Token";
    string  public constant SYMBOL     = "ATC-001";
    uint256 public constant TOTAL_SUPPLY = 1;

    address public holder;
    uint256 public mintedAt;
    bool    public locked;

    // Provenance-Kette (unveränderliche Geschichte)
    struct ProvenanceEntry {
        address from;
        address to;
        uint256 timestamp;
        string  note;
    }
    ProvenanceEntry[] public provenance;

    // ── Events ────────────────────────────────────────────
    event GenesisMinted(address indexed holder, uint256 timestamp);
    event GenesisLocked(uint256 timestamp);
    event ProvenanceRecorded(address indexed from, address indexed to, string note);

    // ── Konstruktor ───────────────────────────────────────
    constructor() Ownable(msg.sender) {
        holder    = msg.sender;
        mintedAt  = block.timestamp;
        locked    = false;

        provenance.push(ProvenanceEntry({
            from:      address(0),
            to:        msg.sender,
            timestamp: block.timestamp,
            note:      "ATC-001 Genesis Mint — A-TownChain Origin"
        }));

        emit GenesisMinted(msg.sender, block.timestamp);
    }

    // ── Sperren (einmalig, permanent) ─────────────────────
    function lock() external onlyOwner {
        require(!locked, "Already locked");
        locked = true;
        emit GenesisLocked(block.timestamp);
    }

    // ── Provenance-Eintrag ────────────────────────────────
    function recordProvenance(address to, string memory note)
        external onlyOwner
    {
        require(!locked, "Token is locked");
        provenance.push(ProvenanceEntry({
            from:      holder,
            to:        to,
            timestamp: block.timestamp,
            note:      note
        }));
        holder = to;
        emit ProvenanceRecorded(msg.sender, to, note);
    }

    // ── Verifizieren ──────────────────────────────────────
    function verify() external view returns (
        bool isValid, address currentHolder,
        uint256 age, uint256 provenanceLen
    ) {
        return (
            true,
            holder,
            block.timestamp - mintedAt,
            provenance.length
        );
    }

    // ── Metadaten ─────────────────────────────────────────
    function getMetadata() external view returns (
        string memory tokenId,
        string memory name_,
        uint256 supply,
        address holdr,
        uint256 created,
        bool    isLocked,
        uint256 provenanceCount
    ) {
        return (
            TOKEN_ID, NAME, TOTAL_SUPPLY,
            holder, mintedAt, locked, provenance.length
        );
    }

    function getProvenance(uint256 index)
        external view returns (ProvenanceEntry memory)
    {
        return provenance[index];
    }

    function provenanceLength() external view returns (uint256) {
        return provenance.length;
    }
}
