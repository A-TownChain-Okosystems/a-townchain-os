"""
A-TownChain — DAO Governance Live (Fix #39)
FFT + ATC Voting | On-Chain Proposals | Quorum | Timelock Execute
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import hashlib, time

DAO_CONFIG = {
    "voting_period":    7 * 86400,    # 7 Tage in Sekunden
    "timelock_delay":   2 * 86400,    # 48h Timelock
    "quorum_fft":       0.10,         # 10% aller FFT
    "quorum_atc":       0.05,         # 5% aller gestakten ATC
    "min_proposal_stake": 1000 * 10**18,  # 1000 ATC zum Proposen
    "max_active_proposals": 10,
    "fft_vote_weight":  1.0,          # 1 FFT = 1 Vote
    "atc_vote_weight":  0.1,          # 10 ATC = 1 Vote
}

@dataclass
class DAOProposal:
    """On-Chain Governance Proposal."""
    proposal_id: str
    proposer:    str
    title:       str
    description: str
    action:      dict       # Was soll ausgeführt werden?
    status:      str = "ACTIVE"  # ACTIVE|PASSED|REJECTED|QUEUED|EXECUTED|EXPIRED
    created_at:  int = field(default_factory=lambda: int(time.time()))
    voting_ends: int = field(default_factory=lambda: int(time.time()) + 7*86400)
    execute_after: Optional[int] = None

    votes_for:   int = 0
    votes_against: int = 0
    votes_abstain: int = 0
    voters:      Dict[str, str] = field(default_factory=dict)  # addr → vote
    total_votes: int = 0

    def is_voting_active(self) -> bool:
        return self.status == "ACTIVE" and time.time() < self.voting_ends

    def get_result(self) -> dict:
        total = self.votes_for + self.votes_against + self.votes_abstain
        support = self.votes_for / total if total > 0 else 0
        return {
            "for":     self.votes_for,
            "against": self.votes_against,
            "abstain": self.votes_abstain,
            "total":   total,
            "support": f"{support*100:.1f}%",
            "passed":  self.votes_for > self.votes_against,
        }

class DAOGovernance:
    """
    A-TownChain DAO Governance — Live-Implementation (Fix #39).

    Stimmgewichtung:
        FFT: 1 FFT = 1 Vote (Franchise-Token)
        ATC: 10 ATC gestakt = 1 Vote

    Lifecycle:
        1. Proposal erstellen (mind. 1000 ATC Stake)
        2. 7 Tage Voting (FFT + ATC gewichtet)
        3. Quorum-Check (10% FFT oder 5% ATC)
        4. 48h Timelock (nach Passing)
        5. Execute (on-chain Aktion)
    """

    def __init__(self, total_fft: int = 100_000_000 * 10**18,
                 total_staked_atc: int = 0):
        self.proposals:       Dict[str, DAOProposal] = {}
        self.total_fft:       int = total_fft
        self.total_staked:    int = total_staked_atc
        self.executed:        set = set()
        self.fft_balances:    Dict[str, int] = {}
        self.staked_atc:      Dict[str, int] = {}
        self._locked:         bool = False

    def _calc_voting_power(self, voter: str) -> int:
        """Berechnet Stimmmacht: FFT-Votes + ATC-Votes."""
        fft_votes = self.fft_balances.get(voter, 0)
        atc_votes = self.staked_atc.get(voter, 0) // (10 * 10**18)
        return int(fft_votes + atc_votes)

    def create_proposal(self, proposer: str, title: str,
                        description: str, action: dict,
                        atc_stake: int) -> DAOProposal:
        """Erstellt neuen Governance-Proposal."""
        min_stake = DAO_CONFIG["min_proposal_stake"]
        if atc_stake < min_stake:
            raise ValueError(f"Zu wenig Stake: {atc_stake//10**18} < {min_stake//10**18} ATC")
        active = [p for p in self.proposals.values() if p.status == "ACTIVE"]
        if len(active) >= DAO_CONFIG["max_active_proposals"]:
            raise ValueError(f"Max aktive Proposals erreicht: {DAO_CONFIG['max_active_proposals']}")
        pid = "PROP_" + hashlib.sha3_256(
            f"{proposer}{title}{time.time()}".encode()).hexdigest()[:16]
        now = int(time.time())
        prop = DAOProposal(
            proposal_id=pid, proposer=proposer,
            title=title, description=description, action=action,
            created_at=now,
            voting_ends=now + DAO_CONFIG["voting_period"],
        )
        self.proposals[pid] = prop
        return prop

    def cast_vote(self, proposal_id: str, voter: str,
                  vote: str) -> dict:
        """Stimme abgeben: 'for' | 'against' | 'abstain'."""
        if self._locked: raise RuntimeError("Reentrancy")
        self._locked = True
        try:
            prop = self.proposals.get(proposal_id)
            if not prop: raise ValueError(f"Proposal nicht gefunden: {proposal_id}")
            if not prop.is_voting_active():
                raise ValueError("Voting-Periode abgelaufen")
            if voter in prop.voters:
                raise ValueError(f"{voter} hat bereits abgestimmt")
            if vote not in ("for", "against", "abstain"):
                raise ValueError(f"Ungültige Stimme: {vote}")

            power = self._calc_voting_power(voter)
            if power == 0:
                raise ValueError("Keine Stimmmacht — FFT oder gestaktes ATC benötigt")

            # State ändern VOR emit
            prop.voters[voter] = vote
            prop.total_votes  += power
            if vote == "for":       prop.votes_for     += power
            elif vote == "against": prop.votes_against += power
            else:                   prop.votes_abstain += power

            return {"voter": voter, "vote": vote,
                    "power": power, "proposal": proposal_id}
        finally:
            self._locked = False

    def finalize_proposal(self, proposal_id: str) -> dict:
        """Schließt Voting ab und prüft Quorum."""
        prop = self.proposals.get(proposal_id)
        if not prop: raise ValueError("Proposal nicht gefunden")
        if prop.is_voting_active():
            raise ValueError("Voting-Periode läuft noch")
        if prop.status != "ACTIVE":
            raise ValueError(f"Bereits finalisiert: {prop.status}")

        # Quorum-Check
        quorum_fft = self.total_fft * DAO_CONFIG["quorum_fft"]
        quorum_atc = self.total_staked * DAO_CONFIG["quorum_atc"]
        quorum_met = prop.total_votes >= min(quorum_fft, max(quorum_atc, 1))

        passed = quorum_met and prop.votes_for > prop.votes_against

        if passed:
            prop.status        = "QUEUED"
            prop.execute_after = int(time.time()) + DAO_CONFIG["timelock_delay"]
        else:
            prop.status = "REJECTED"

        return {
            "proposal_id": proposal_id,
            "passed":      passed,
            "quorum_met":  quorum_met,
            "status":      prop.status,
            "result":      prop.get_result(),
            "execute_after": prop.execute_after,
        }

    def execute_proposal(self, proposal_id: str,
                          executor: str) -> dict:
        """Führt Proposal nach Timelock aus."""
        prop = self.proposals.get(proposal_id)
        if not prop: raise ValueError("Proposal nicht gefunden")
        if prop.status != "QUEUED":
            raise ValueError(f"Nicht in Queue: {prop.status}")
        if prop.execute_after and time.time() < prop.execute_after:
            remaining = prop.execute_after - time.time()
            raise ValueError(f"Timelock läuft noch: {remaining/3600:.1f}h")
        if proposal_id in self.executed:
            raise ValueError("Bereits ausgeführt")

        self.executed.add(proposal_id)
        prop.status = "EXECUTED"

        return {
            "proposal_id": proposal_id,
            "executed_by": executor,
            "action":      prop.action,
            "status":      "EXECUTED",
            "timestamp":   int(time.time()),
        }

    def get_governance_stats(self) -> dict:
        total  = len(self.proposals)
        active = len([p for p in self.proposals.values() if p.status == "ACTIVE"])
        done   = len([p for p in self.proposals.values() if p.status == "EXECUTED"])
        return {
            "total_proposals": total,
            "active":          active,
            "executed":        done,
            "total_fft":       self.total_fft // 10**18,
            "total_staked_atc":self.total_staked // 10**18,
            "config":          DAO_CONFIG,
        }
