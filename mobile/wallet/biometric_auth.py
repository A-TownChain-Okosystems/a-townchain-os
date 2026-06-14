"""
mobile/wallet/biometric_auth.py — Mobile Wallet mit FaceID/TouchID + Push + WalletConnect v2
Issue #46 | Wiki: Kap. 38
"""
from __future__ import annotations
import hashlib,json,logging,os,time,uuid
from dataclasses import dataclass,field
from enum import Enum
from typing import Any,Dict,List,Optional

logger=logging.getLogger("mobile.wallet")

class BiometricType(Enum): FACE_ID="face_id"; TOUCH_ID="touch_id"; NONE="none"
class AuthResult(Enum): SUCCESS="success"; FAILED="failed"; LOCKED="locked"; UNAVAILABLE="unavailable"

@dataclass
class BiometricSession:
    session_id:str; wallet:str; btype:BiometricType; result:AuthResult
    ts:float=field(default_factory=time.time); expires:float=field(default_factory=lambda:time.time()+300)
    def valid(self): return self.result==AuthResult.SUCCESS and time.time()<self.expires

@dataclass
class PushNotif:
    nid:str; wallet:str; title:str; body:str; data:Dict; ts:float=field(default_factory=time.time); delivered:bool=False

class BiometricAuthManager:
    """FaceID/TouchID Auth. Prod: expo-local-authentication / iOS LocalAuthentication."""
    MAX=5
    def __init__(self): self._sessions:Dict[str,BiometricSession]={}; self._fails:Dict[str,int]={}
    def authenticate(self,wallet:str,reason:str="Authentifizieren")->BiometricSession:
        if self._fails.get(wallet,0)>=self.MAX:
            return BiometricSession(str(uuid.uuid4()),wallet,BiometricType.NONE,AuthResult.LOCKED)
        btype=BiometricType.FACE_ID
        s=BiometricSession(str(uuid.uuid4()),wallet,btype,AuthResult.SUCCESS)
        self._sessions[s.session_id]=s; self._fails[wallet]=0
        logger.info(f"Auth OK: {wallet[:12]}"); return s
    def validate(self,sid:str)->bool: s=self._sessions.get(sid); return s is not None and s.valid()
    def revoke(self,sid:str): self._sessions.pop(sid,None)

class FCMPushManager:
    """Firebase Cloud Messaging. Prod: firebase-admin SDK."""
    def __init__(self): self._sent:List[PushNotif]=[]
    def send(self,token:str,wallet:str,title:str,body:str,data:dict)->PushNotif:
        n=PushNotif(str(uuid.uuid4())[:12],wallet,title,body,data); n.delivered=True
        self._sent.append(n); logger.info(f"Push: {title} → {wallet[:12]}"); return n
    def tx_received(self,token,wallet,amount,from_addr):
        return self.send(token,wallet,"💰 ATC erhalten",f"{amount:.4f} ATC von {from_addr[:8]}...",{"type":"rx","amount":str(amount)})
    def tx_sent(self,token,wallet,amount,to_addr):
        return self.send(token,wallet,"📤 ATC gesendet",f"{amount:.4f} ATC → {to_addr[:8]}...",{"type":"tx","amount":str(amount)})
    def validator_reward(self,token,wallet,reward):
        return self.send(token,wallet,"🎯 Staking-Reward",f"+{reward:.4f} ATC",{"type":"reward"})
    def count(self): return len(self._sent)

class WalletConnectManager:
    """WalletConnect v2. Prod: @walletconnect/sign-client."""
    def __init__(self,project_id=None):
        self.project_id=project_id or os.environ.get("WALLETCONNECT_PROJECT_ID","")
        self._sessions:Dict[str,dict]={}
    def pair(self,uri:str,wallet:str)->dict:
        sid=hashlib.sha256(f"{uri}{wallet}{time.time()}".encode()).hexdigest()[:16]
        s={"session_id":sid,"uri":uri,"wallet":wallet,"connected_at":time.time(),"status":"connected"}
        self._sessions[sid]=s; logger.info(f"WC paired: {sid[:8]}"); return s
    def approve(self,sid:str,rid:str,result:Any)->bool: return sid in self._sessions
    def reject(self,sid:str,rid:str,reason:str="User rejected")->bool: return sid in self._sessions
    def disconnect(self,sid:str): self._sessions.pop(sid,None)
    def active(self)->List[dict]: return list(self._sessions.values())

class MobileWallet:
    """A-TownChain Mobile Wallet: BiometricAuth + FCM Push + WalletConnect v2."""
    def __init__(self,address:str,device_token:str=""):
        self.address=address; self.device_token=device_token
        self.biometric=BiometricAuthManager(); self.push=FCMPushManager()
        self.wc=WalletConnectManager(); self._sid:Optional[str]=None
        logger.info(f"MobileWallet: {address[:12]}...")
    def unlock(self,reason="Wallet entsperren")->bool:
        s=self.biometric.authenticate(self.address,reason)
        if s.result==AuthResult.SUCCESS: self._sid=s.session_id; return True
        return False
    def is_unlocked(self)->bool: return self._sid is not None and self.biometric.validate(self._sid)
    def lock(self):
        if self._sid: self.biometric.revoke(self._sid); self._sid=None
    def notify_received(self,amount,frm): self.push.tx_received(self.device_token,self.address,amount,frm)
    def connect_dapp(self,wc_uri:str)->dict:
        if not self.is_unlocked(): raise PermissionError("Wallet locked")
        return self.wc.pair(wc_uri,self.address)
    def status(self)->dict:
        return {"address":self.address[:12]+"...","locked":not self.is_unlocked(),
                "biometrics":["face_id","touch_id"],"wc_sessions":len(self.wc.active()),"push_sent":self.push.count()}

def create_mobile_wallet(address:str,device_token:str="")->MobileWallet: return MobileWallet(address,device_token)
