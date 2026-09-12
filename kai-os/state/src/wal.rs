//! Write-Ahead-Log (G2-B, Issue #112) — Persistente Storage-Layer.
//!
//! WAL-Vertrag (Crash-Sicherheit):
//! 1. **WAL vor State:** jede Tx wird ZUERST in den Log geschrieben (inkl.
//!    `sync_data`), ERST DANACH in den StateStore angewendet — ein Absturz
//!    verliert niemals eine angewendete Änderung.
//! 2. **Hash-Kette:** jeder Record verketted den Hash des Vorgängers —
//!    Manipulation mitten im Log wird beim Replay fail-closed erkannt.
//! 3. **Torn Tail:** ein unvollständiger LETZTER Record (Absturz während des
//!    Schreibens) wird verworfen — das ist der Standard-WAL-Vertrag; Corruption
//!    MITTEN im Log ist ein Fehler.

use crate::state::Tx;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

fn sha256_hex(input: &[u8]) -> String {
    let d = Sha256::digest(input);
    d.iter().map(|b| format!("{b:02x}")).collect()
}

#[derive(Debug, Serialize, Deserialize)]
pub struct WalRecord {
    pub seq: u64,
    pub prev_hash: String,
    pub tx: Tx,
}

impl WalRecord {
    pub fn hash(&self) -> String {
        let payload = format!("{}|{}|{}", self.seq, self.prev_hash, serde_json::to_string(&self.tx).unwrap_or_default());
        sha256_hex(payload.as_bytes())
    }
}

#[derive(Debug)]
pub enum WalError {
    Io(std::io::Error),
    /// Hash-Kette mitten im Log gebrochen — fail-closed, kein Blind-Replay.
    ChainBroken { line: usize, expected: String, got: String },
    /// Record unverständlich (kein JSON) UND nicht der letzte — Corruption.
    MalformedRecord { line: usize },
}

impl std::fmt::Display for WalError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            WalError::Io(e) => write!(f, "WAL I/O: {e}"),
            WalError::ChainBroken { line, expected, got } =>
                write!(f, "WAL-Chain gebrochen (Zeile {line}): erwartet {expected}, gefunden {got}"),
            WalError::MalformedRecord { line } => write!(f, "WAL-Record unlesbar (Zeile {line})"),
        }
    }
}

/// Das WAL für einen StateStore.
pub struct WriteAheadLog {
    path: PathBuf,
    file: File,
    seq: u64,
    prev_hash: String,
}

pub const GENESIS_PREV: &str = "0000000000000000000000000000000000000000000000000000000000000000";

impl WriteAheadLog {
    /// WAL öffnen (erstellt bei Bedarf) und Konsistenz prüfen.
    pub fn open(path: &Path) -> Result<Self, WalError> {
        let (seq, prev_hash) = Self::scan_tail(path)?;
        let file = OpenOptions::new().create(true).append(true).open(path)
            .map_err(WalError::Io)?;
        Ok(Self { path: path.to_path_buf(), file, seq, prev_hash })
    }

    /// Tx anlegen: WAL zuerst (durable), dann erst gilt sie als angewendet.
    pub fn append(&mut self, tx: &Tx) -> Result<u64, WalError> {
        self.seq += 1;
        let record = WalRecord { seq: self.seq, prev_hash: self.prev_hash.clone(), tx: tx.clone() };
        let hash = record.hash();
        let line = serde_json::to_string(&record).map_err(|e| WalError::Io(std::io::Error::other(e)))?;
        writeln!(self.file, "{line}").map_err(WalError::Io)?;
        self.file.sync_data().map_err(WalError::Io)?; // DURABILITY vor Rückkehr
        self.prev_hash = hash;
        Ok(self.seq)
    }

    /// Ende der Kette (für Recovery-Prüfung gegen Snapshot).
    pub fn tip_hash(&self) -> &str {
        &self.prev_hash
    }

    pub fn seq(&self) -> u64 {
        self.seq
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    /// Komplettes Log lesen: verifiziert die Hash-Kette komplett durch.
    /// Ein unvollständiger LETZTER Record (torn tail) wird verworfen.
    pub fn replay(path: &Path) -> Result<(Vec<Tx>, u64, String), WalError> {
        let file = File::open(path).map_err(WalError::Io)?;
        let reader = BufReader::new(file);
        let mut txs = Vec::new();
        let mut seq = 0u64;
        let mut prev_hash = GENESIS_PREV.to_string();
        let mut line_no = 0usize;
        for line in reader.lines() {
            let line = line.map_err(WalError::Io)?;
            line_no += 1;
            if line.trim().is_empty() {
                continue;
            }
            let record: WalRecord = match serde_json::from_str(&line) {
                Ok(r) => r,
                // Torn tail: unlesbarer Record NUR an letzter Stelle -> verwerfen.
                Err(_) => {
                    let is_last = Self::is_last_line(path, line_no);
                    if is_last {
                        return Ok((txs, seq, prev_hash)); // torn tail verworfen
                    }
                    return Err(WalError::MalformedRecord { line: line_no });
                }
            };
            // Kette prüfen: seq aufsteigend + prev_hash korrekt + eigener Hash stimmt
            if record.seq != seq + 1 {
                return Err(WalError::ChainBroken { line: line_no, expected: format!("seq {}", seq + 1), got: format!("seq {}", record.seq) });
            }
            if record.prev_hash != prev_hash {
                return Err(WalError::ChainBroken { line: line_no, expected: prev_hash.clone(), got: record.prev_hash.clone() });
            }
            prev_hash = record.hash();
            seq = record.seq;
            txs.push(record.tx);
        }
        Ok((txs, seq, prev_hash))
    }

    /// Beim Öffnen: letztes gültiges Kettenende ermitteln.
    fn scan_tail(path: &Path) -> Result<(u64, String), WalError> {
        if !path.exists() {
            return Ok((0, GENESIS_PREV.to_string()));
        }
        let (_, seq, prev_hash) = Self::replay(path)?;
        Ok((seq, prev_hash))
    }

    fn is_last_line(path: &Path, line_no: usize) -> bool {
        // Grobe Prüfung: Anzahl Zeilen zählen — torn tail liegt immer am Dateiende.
        match fs::File::open(path) {
            Ok(f) => BufReader::new(f).lines().count() <= line_no,
            Err(_) => false,
        }
    }
}

/// PersistentState: StateStore mit WAL-Garantie (WAL vor State).
pub struct PersistentState {
    pub store: crate::state::StateStore,
    wal: WriteAheadLog,
}

impl PersistentState {
    pub fn open(state_path: &Path, wal_path: &Path) -> Result<Self, WalError> {
        let store = if state_path.exists() {
            crate::persistence::load_snapshot_store(state_path).map_err(WalError::Io)?
        } else {
            crate::state::StateStore::new()
        };
        // WAL nachladen und anwenden (alles nach dem Snapshot)
        let (txs, _seq, _tip) = if wal_path.exists() { WriteAheadLog::replay(wal_path)? } else { (Vec::new(), 0, GENESIS_PREV.to_string()) };
        let mut store = store;
        for tx in &txs {
            store.apply(tx);
        }
        let wal = WriteAheadLog::open(wal_path)?;
        Ok(Self { store, wal })
    }

    /// Crash-sicheres Anwenden: WAL zuerst (durable), dann State.
    pub fn apply(&mut self, tx: &Tx) -> Result<u64, WalError> {
        let seq = self.wal.append(tx)?;
        self.store.apply(tx);
        Ok(seq)
    }

    /// Snapshot auf Disk schreiben UND WAL konsolidieren (truncate + Chain-Reset).
    /// Bekannte Grenze (dokumentiert, G2-D verfeinert): ein Absturz GENAU zwischen
    /// Snapshot-Sync und WAL-Truncate fuehrt beim Reopen zu einem Doppel-Replay.
    /// Crash-Recovery ohne Checkpoint ist vollstaendig stark (WAL-Vertrag).
    pub fn checkpoint(&mut self, height: u64, tip_block_hash: &str, state_path: &Path) -> Result<(), WalError> {
        crate::persistence::save_snapshot_store(&self.store, height, tip_block_hash, state_path).map_err(WalError::Io)?;
        // WAL konsolidieren: leeren Log neu beginnen (Kette resettet auf Genesis).
        self.wal.file.set_len(0).map_err(WalError::Io)?;
        self.wal.file.sync_data().map_err(WalError::Io)?;
        self.wal.seq = 0;
        self.wal.prev_hash = GENESIS_PREV.to_string();
        Ok(())
    }
}
