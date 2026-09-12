//! Peer-Authentifizierung: Challenge-Response mit Ed25519 + Replay-Schutz.
//! Nonces müssen pro Initiator strikt monoton steigern — Wiederholung = Replay.

use crate::peer::verify_signature;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Challenge {
    pub from_peer_id: String,
    pub to_peer_id: String,
    pub nonce: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChallengeResponse {
    pub from_peer_id: String,
    pub to_peer_id: String,
    pub nonce: u64,
    pub signature: Vec<u8>,
}

#[derive(Debug)]
pub enum AuthError {
    Replay { nonce: u64, last: u64 },
    WrongPeer { expected: String, got: String },
    BadSignature,
}

impl std::fmt::Display for AuthError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AuthError::Replay { nonce, last } => write!(f, "replay: nonce {nonce} <= last {last}"),
            AuthError::WrongPeer { expected, got } => {
                write!(f, "wrong peer: expected {expected}, got {got}")
            }
            AuthError::BadSignature => write!(f, "signature verification failed"),
        }
    }
}

/// Signiert die kanonische Challenge-Payload (deterministisch).
pub fn challenge_payload(c: &Challenge) -> Vec<u8> {
    let d = Sha256::digest(format!("{}|{}|{}", c.from_peer_id, c.to_peer_id, c.nonce).as_bytes());
    d.to_vec()
}

/// Initiator-seitige Challenge-Erzeugung mit strikt monotoner Nonce.
pub struct ChallengeGenerator {
    last_nonce: u64,
}

impl ChallengeGenerator {
    pub fn new() -> Self {
        Self { last_nonce: 0 }
    }

    pub fn next(&mut self, from: &str, to: &str) -> Challenge {
        self.last_nonce += 1;
        Challenge {
            from_peer_id: from.into(),
            to_peer_id: to.into(),
            nonce: self.last_nonce,
        }
    }
}

/// Responder: Challenge mit eigenem Key beantworten.
pub fn respond(challenge: &Challenge, responder: &crate::peer::Keypair) -> ChallengeResponse {
    let payload = challenge_payload(challenge);
    let signature = responder.sign(&payload).to_vec();
    ChallengeResponse {
        from_peer_id: challenge.to_peer_id.clone(),
        to_peer_id: challenge.from_peer_id.clone(),
        nonce: challenge.nonce,
        signature,
    }
}

/// Initiator: Response verifizieren — PeerId, Nonce-Monotonie und Signatur.
pub struct AuthRegistry {
    last_nonce: HashMap<String, u64>,
}

impl AuthRegistry {
    pub fn new() -> Self {
        Self {
            last_nonce: HashMap::new(),
        }
    }

    pub fn verify(
        &mut self,
        challenge: &Challenge,
        response: &ChallengeResponse,
        responder_public: &[u8; 32],
    ) -> Result<(), AuthError> {
        if response.to_peer_id != challenge.from_peer_id
            || response.from_peer_id != challenge.to_peer_id
        {
            return Err(AuthError::WrongPeer {
                expected: challenge.to_peer_id.clone(),
                got: response.from_peer_id.clone(),
            });
        }
        let last = self
            .last_nonce
            .get(&response.from_peer_id)
            .copied()
            .unwrap_or(0);
        if response.nonce <= last {
            return Err(AuthError::Replay {
                nonce: response.nonce,
                last,
            });
        }
        let payload = challenge_payload(challenge);
        let sig: [u8; 64] = match response.signature.clone().try_into() {
            Ok(s) => s,
            Err(_) => return Err(AuthError::BadSignature),
        };
        if !verify_signature(responder_public, &payload, &sig) {
            return Err(AuthError::BadSignature);
        }
        self.last_nonce
            .insert(response.from_peer_id.clone(), response.nonce);
        Ok(())
    }
}

/// Session-ID: deterministische Ableitung aus den beiden Peers + Nonce.
pub fn session_id(a: &str, b: &str, nonce: u64) -> String {
    let d = Sha256::digest(format!("{a}|{b}|{nonce}").as_bytes());
    crate::hex(&d)
}
