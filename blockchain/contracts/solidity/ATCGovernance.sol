// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ATCGovernance
 * @dev ATC-9900 DAO — Dezentrale Abstimmungen für A-TownChain
 * Quorum: 10% der zirkulierenden Supply
 * Voting-Period: 7 Tage (konfigurierbar)
 * Proposal-Deposit: 1.000 ATC
 * Timelock: 48h vor Execution
 */
contract ATCGovernance is Ownable, ReentrancyGuard {

    // ── Konstanten ────────────────────────────────────────
    uint256 public constant QUORUM_BPS       = 1000;        // 10% = 1000/10000
    uint256 public constant PROPOSAL_DEPOSIT = 1_000 ether; // 1.000 ATC
    uint256 public constant VOTING_PERIOD    = 7 days;
    uint256 public constant TIMELOCK         = 48 hours;
    uint256 public constant MAX_OPTIONS      = 10;

    // ── State ─────────────────────────────────────────────
    IERC20 public atcToken;
    uint256 private _proposalCount;

    enum Status { Active, Passed, Failed, Executed, Cancelled }

    struct Proposal {
        uint256   id;
        address   creator;
        string    title;
        string    description;
        string[]  options;
        uint256   deadline;
        uint256   executionTime;  // deadline + TIMELOCK
        Status    status;
        uint256   totalVotes;
        uint256   winningOption;
        bool      depositReturned;
    }

    mapping(uint256 => Proposal)                    public proposals;
    mapping(uint256 => mapping(uint256 => uint256)) public optionVotes;   // proposalId → option → votes
    mapping(uint256 => mapping(address => bool))    public hasVoted;
    mapping(uint256 => mapping(address => uint256)) public voterOption;

    // ── Events ────────────────────────────────────────────
    event ProposalCreated(uint256 indexed id, address indexed creator,
                          string title, uint256 deadline);
    event Voted(uint256 indexed proposalId, address indexed voter,
                uint256 option, uint256 votingPower);
    event ProposalFinalized(uint256 indexed id, Status status,
                            string winningOption);
    event ProposalExecuted(uint256 indexed id);

    // ── Konstruktor ───────────────────────────────────────
    constructor(address _atcToken) Ownable(msg.sender) {
        atcToken = IERC20(_atcToken);
    }

    // ── Proposal erstellen ────────────────────────────────
    function createProposal(
        string   memory title,
        string   memory description,
        string[] memory options
    ) external nonReentrant returns (uint256) {
        require(options.length >= 2 && options.length <= MAX_OPTIONS, "Invalid options count");
        require(bytes(title).length > 0, "Empty title");

        // Deposit abziehen
        require(
            atcToken.transferFrom(msg.sender, address(this), PROPOSAL_DEPOSIT),
            "Deposit transfer failed"
        );

        uint256 id = _proposalCount++;
        Proposal storage p = proposals[id];
        p.id            = id;
        p.creator       = msg.sender;
        p.title         = title;
        p.description   = description;
        p.options       = options;
        p.deadline      = block.timestamp + VOTING_PERIOD;
        p.executionTime = block.timestamp + VOTING_PERIOD + TIMELOCK;
        p.status        = Status.Active;

        emit ProposalCreated(id, msg.sender, title, p.deadline);
        return id;
    }

    // ── Abstimmen ─────────────────────────────────────────
    function vote(uint256 proposalId, uint256 option) external nonReentrant {
        Proposal storage p = proposals[proposalId];
        require(p.status == Status.Active, "Not active");
        require(block.timestamp < p.deadline, "Voting ended");
        require(!hasVoted[proposalId][msg.sender], "Already voted");
        require(option < p.options.length, "Invalid option");

        uint256 power = atcToken.balanceOf(msg.sender);
        require(power > 0, "No voting power");

        hasVoted[proposalId][msg.sender]  = true;
        voterOption[proposalId][msg.sender] = option;
        optionVotes[proposalId][option]  += power;
        p.totalVotes                     += power;

        emit Voted(proposalId, msg.sender, option, power);
    }

    // ── Finalisieren ──────────────────────────────────────
    function finalize(uint256 proposalId) external {
        Proposal storage p = proposals[proposalId];
        require(p.status == Status.Active, "Not active");
        require(block.timestamp >= p.deadline, "Voting not ended");

        uint256 totalSupply = atcToken.totalSupply();
        uint256 quorum      = (totalSupply * QUORUM_BPS) / 10_000;

        if (p.totalVotes < quorum) {
            p.status = Status.Failed;
            // Deposit → bleibt im Contract (Anti-Spam)
            emit ProposalFinalized(proposalId, Status.Failed, "");
            return;
        }

        // Gewinner ermitteln
        uint256 bestOption = 0;
        uint256 bestVotes  = 0;
        for (uint256 i = 0; i < p.options.length; i++) {
            if (optionVotes[proposalId][i] > bestVotes) {
                bestVotes  = optionVotes[proposalId][i];
                bestOption = i;
            }
        }
        p.status        = Status.Passed;
        p.winningOption = bestOption;

        emit ProposalFinalized(proposalId, Status.Passed, p.options[bestOption]);
    }

    // ── Execution (nach Timelock) ─────────────────────────
    function execute(uint256 proposalId) external nonReentrant {
        Proposal storage p = proposals[proposalId];
        require(p.status == Status.Passed, "Not passed");
        require(block.timestamp >= p.executionTime, "Timelock active");

        p.status = Status.Executed;

        // Deposit an Creator zurück
        if (!p.depositReturned) {
            p.depositReturned = true;
            atcToken.transfer(p.creator, PROPOSAL_DEPOSIT);
        }
        emit ProposalExecuted(proposalId);
    }

    // ── Views ─────────────────────────────────────────────
    function getProposal(uint256 id)
        external view returns (Proposal memory)
    { return proposals[id]; }

    function getOptionVotes(uint256 proposalId, uint256 option)
        external view returns (uint256)
    { return optionVotes[proposalId][option]; }

    function proposalCount() external view returns (uint256) { return _proposalCount; }

    function getStats() external view returns (
        uint256 total, uint256 active, uint256 passed, uint256 failed
    ) {
        for (uint256 i = 0; i < _proposalCount; i++) {
            total++;
            Status s = proposals[i].status;
            if (s == Status.Active)  active++;
            if (s == Status.Passed || s == Status.Executed) passed++;
            if (s == Status.Failed)  failed++;
        }
    }
}
