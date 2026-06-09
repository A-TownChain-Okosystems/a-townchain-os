"""
Governance Contract — Issue #9 (ATC-9900 DAO)
Vollständiges On-Chain Voting: Proposals, Abstimmung, Execution.
"""
import hashlib, time, json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from enum import Enum

class ProposalStatus(Enum):
    PENDING   = "pending"
    ACTIVE    = "active"
    PASSED    = "passed"
    REJECTED  = "rejected"
    EXECUTED  = "executed"
    EXPIRED   = "expired"

class VoteChoice(Enum):
    YES     = "yes"
    NO      = "no"
    ABSTAIN = "abstain"

@dataclass
class Vote:
    voter:    str
    choice:   VoteChoice
    weight:   float    # Token-Gewichtung
    ts:       float = field(default_factory=time.time)

@dataclass
class Proposal:
    id:          str
    title:       str
    description: str
    proposer:    str
    action:      dict     # was ausgeführt werden soll
    created:     float
    voting_end:  float
    quorum:      float = 0.10    # 10% der Token müssen abstimmen
    threshold:   float = 0.51    # >51% YES zum Bestehen
    status:      ProposalStatus = ProposalStatus.ACTIVE
    votes:       Dict[str, Vote] = field(default_factory=dict)
    executed_at: Optional[float] = None

    def tally(self):
        yes = sum(v.weight for v in self.votes.values() if v.choice == VoteChoice.YES)
        no  = sum(v.weight for v in self.votes.values() if v.choice == VoteChoice.NO)
        abs = sum(v.weight for v in self.votes.values() if v.choice == VoteChoice.ABSTAIN)
        total = yes + no + abs
        return {"yes": yes, "no": no, "abstain": abs, "total": total,
                "yes_pct": yes/total*100 if total else 0,
                "no_pct":  no/total*100  if total else 0}

class GovernanceContract:
    """
    ATC-9900 DAO Governance.
    Jeder Token-Inhaber kann Proposals erstellen & abstimmen.
    Voting-Power = ATC-Balance (Token-gewichtet).
    """
    MIN_PROPOSAL_TOKENS = 1000.0   # min. 1000 ATC für Proposal
    VOTING_PERIOD       = 7 * 86400  # 7 Tage

    def __init__(self, owner: str, total_supply: float = 1_000_000):
        self.owner         = owner
        self.total_supply  = total_supply
        self._proposals:   Dict[str, Proposal] = {}
        self._balances:    Dict[str, float]     = {}

    def _prop_id(self, title, proposer):
        return hashlib.sha256(f"{title}{proposer}{time.time()}".encode()).hexdigest()[:16]

    def set_balance(self, addr: str, amount: float):
        """Testnet: Balance direkt setzen."""
        self._balances[addr] = amount

    def get_balance(self, addr: str) -> float:
        return self._balances.get(addr, 0.0)

    def create_proposal(self, proposer: str, title: str,
                         description: str, action: dict,
                         voting_days: int = 7) -> Proposal:
        bal = self.get_balance(proposer)
        if bal < self.MIN_PROPOSAL_TOKENS:
            raise ValueError(f"Mindestens {self.MIN_PROPOSAL_TOKENS} ATC nötig (du hast {bal})")

        pid = self._prop_id(title, proposer)
        p   = Proposal(
            id=pid, title=title, description=description,
            proposer=proposer, action=action,
            created=time.time(),
            voting_end=time.time() + voting_days*86400,
        )
        self._proposals[pid] = p
        return p

    def vote(self, proposal_id: str, voter: str, choice: VoteChoice) -> bool:
        p = self._proposals.get(proposal_id)
        if not p: raise ValueError("Proposal nicht gefunden")
        if p.status != ProposalStatus.ACTIVE: raise ValueError("Proposal nicht aktiv")
        if time.time() > p.voting_end:
            p.status = ProposalStatus.EXPIRED; raise ValueError("Abstimmungsfrist abgelaufen")
        if voter in p.votes: raise ValueError("Bereits abgestimmt")

        weight = self.get_balance(voter)
        if weight <= 0: raise ValueError("Keine Stimmrechte (kein ATC-Balance)")

        p.votes[voter] = Vote(voter=voter, choice=choice, weight=weight)
        return True

    def finalize(self, proposal_id: str) -> ProposalStatus:
        p = self._proposals.get(proposal_id)
        if not p: raise ValueError("Proposal nicht gefunden")
        if p.status != ProposalStatus.ACTIVE: return p.status
        if time.time() < p.voting_end: raise ValueError("Abstimmung läuft noch")

        tally     = p.tally()
        voted_pct = tally["total"] / self.total_supply
        if voted_pct < p.quorum:
            p.status = ProposalStatus.REJECTED  # Quorum nicht erreicht
        elif tally["yes"] > tally["no"] * (p.threshold / (1 - p.threshold)):
            p.status = ProposalStatus.PASSED
        else:
            p.status = ProposalStatus.REJECTED
        return p.status

    def execute(self, proposal_id: str, executor: str) -> dict:
        p = self._proposals.get(proposal_id)
        if not p: raise ValueError("Proposal nicht gefunden")
        if p.status != ProposalStatus.PASSED: raise ValueError("Nur PASSED Proposals ausführbar")
        p.status      = ProposalStatus.EXECUTED
        p.executed_at = time.time()
        return {"executed": True, "action": p.action, "by": executor, "at": p.executed_at}

    def get_proposal(self, pid: str) -> Optional[Proposal]: return self._proposals.get(pid)

    def list_proposals(self, status: Optional[ProposalStatus] = None) -> List[Proposal]:
        props = list(self._proposals.values())
        if status: props = [p for p in props if p.status == status]
        return sorted(props, key=lambda p: p.created, reverse=True)

    def stats(self) -> dict:
        props = list(self._proposals.values())
        return {
            "total": len(props),
            "active":   sum(1 for p in props if p.status==ProposalStatus.ACTIVE),
            "passed":   sum(1 for p in props if p.status==ProposalStatus.PASSED),
            "executed": sum(1 for p in props if p.status==ProposalStatus.EXECUTED),
            "rejected": sum(1 for p in props if p.status==ProposalStatus.REJECTED),
        }
