"""
blockchain/zkp/groth16.py — Groth16 ZKP für A-TownChain OS (Issue #47, Kap. 25)
Privacy-Transaktionen via Zero-Knowledge Proofs.
Produktion-Upgrade: _mock_prove() → Circom/snarkjs CLI
"""
from __future__ import annotations
import hashlib, json, logging, os, time, uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger("blockchain.zkp")

@dataclass
class Groth16Proof:
    pi_a: List[str]; pi_b: List[List[str]]; pi_c: List[str]
    public_signals: List[str]
    protocol: str = "groth16"; curve: str = "bn128"; circuit_id: str = "atc_balance_v1"
    created_at: float = field(default_factory=time.time)
    def to_dict(self): return {"pi_a":self.pi_a,"pi_b":self.pi_b,"pi_c":self.pi_c,"public_signals":self.public_signals,"protocol":self.protocol}
    def hash(self): return hashlib.sha256(json.dumps(self.to_dict(),sort_keys=True).encode()).hexdigest()

@dataclass
class ShieldedTransaction:
    tx_id: str; sender_commit: str; recipient_commit: str
    amount_commit: str; nullifier: str
    proof: Optional[Groth16Proof] = None
    timestamp: float = field(default_factory=time.time); verified: bool = False
    def to_dict(self):
        return {"tx_id":self.tx_id,"sender":self.sender_commit,"amount":self.amount_commit,
                "nullifier":self.nullifier,"proof_hash":self.proof.hash() if self.proof else None,"verified":self.verified}

class PedersenCommitment:
    G=7919; H=6271; P=2**255-19
    @classmethod
    def commit(cls,v,r): return hex((v*cls.G+r*cls.H)%cls.P)

class NullifierSet:
    def __init__(self,path="/tmp/atc_nullifiers.json"):
        self._path=path; self._n: set = self._load()
    def _load(self):
        try: return set(json.load(open(self._path))) if os.path.exists(self._path) else set()
        except: return set()
    def _save(self): json.dump(list(self._n),open(self._path,"w"))
    def add(self,n):
        if n in self._n: return False
        self._n.add(n); self._save(); return True
    def contains(self,n): return n in self._n
    def size(self): return len(self._n)

class Groth16Prover:
    def __init__(self,circuit="atc_balance_v1"):
        self.circuit=circuit; self._count=0
    def prove_balance(self,balance:int,amount:int,blinding:int)->Tuple["Groth16Proof",str]:
        assert amount>0 and balance>=amount,"Invalid balance/amount"
        r1=int(hashlib.sha256(f"{blinding}1".encode()).hexdigest(),16)%(2**32)
        r2=int(hashlib.sha256(f"{blinding}2".encode()).hexdigest(),16)%(2**32)
        c_b=PedersenCommitment.commit(balance,r1)
        c_a=PedersenCommitment.commit(amount,r2)
        c_c=PedersenCommitment.commit(balance-amount,r1+r2)
        null=hashlib.sha256(f"{blinding}-{balance}-{amount}".encode()).hexdigest()
        seed=hashlib.sha256(f"{c_b}{c_a}{c_c}".encode()).hexdigest()
        proof=Groth16Proof(pi_a=[seed[:32],seed[32:64],"1"],pi_b=[[seed[16:48],seed[48:64]],[seed[:16],seed[32:48]],["1","0"]],pi_c=[seed[8:40],seed[40:64],"1"],public_signals=[c_b,c_a,c_c,null])
        self._count+=1; return proof,null

class Groth16Verifier:
    def __init__(self): self._count=0
    def verify(self,proof:Groth16Proof)->bool:
        ok=(len(proof.pi_a)==3 and len(proof.pi_b)==3 and len(proof.pi_c)==3 and bool(proof.public_signals))
        if ok: self._count+=1
        return ok
    def stats(self): return {"verified":self._count}

class ZKPLayer:
    def __init__(self):
        self.prover=Groth16Prover(); self.verifier=Groth16Verifier(); self.nullifiers=NullifierSet()
        logger.info("ZKP L0 Layer initialized (groth16/bn128)")
    def create_shielded_tx(self,balance:int,amount:int,recipient:str,blinding:int=None)->Optional[ShieldedTransaction]:
        if blinding is None: blinding=int(hashlib.sha256(os.urandom(32)).hexdigest(),16)%(2**32)
        try: proof,null=self.prover.prove_balance(balance,amount,blinding)
        except AssertionError as e: logger.error(f"ZKP failed:{e}"); return None
        tx_id=hashlib.sha256(f"{null}{time.time()}".encode()).hexdigest()[:32]
        return ShieldedTransaction(tx_id=tx_id,sender_commit=PedersenCommitment.commit(balance,blinding),
            recipient_commit=hashlib.sha256(recipient.encode()).hexdigest(),
            amount_commit=PedersenCommitment.commit(amount,blinding+1),nullifier=null,proof=proof)
    def verify_shielded_tx(self,tx:ShieldedTransaction)->bool:
        if self.nullifiers.contains(tx.nullifier): logger.warning("Double-spend!"); return False
        if not tx.proof or not self.verifier.verify(tx.proof): return False
        self.nullifiers.add(tx.nullifier); tx.verified=True; return True
    def status(self): return {"active":True,"protocol":"groth16","curve":"bn128","nullifiers":self.nullifiers.size(),**self.verifier.stats()}

_zkp:Optional[ZKPLayer]=None
def get_zkp_layer()->ZKPLayer:
    global _zkp
    if _zkp is None: _zkp=ZKPLayer()
    return _zkp
