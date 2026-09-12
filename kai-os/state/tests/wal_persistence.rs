//! G2-B (Issue #112): WAL + Snapshot-Persistenz + Crash-Recovery.
//! Echter Dateisystem-Test — der "Absturz" ist ein echter Drop,
//! die Recovery liest von Disk. Deterministisch (REQ-ENG-002).

use kai_os_state::persistence::{load_snapshot_store, save_snapshot_store, snapshot_meta};
use kai_os_state::state::{StateStore, Tx};
use kai_os_state::wal::{PersistentState, WalError, WriteAheadLog};
use std::path::PathBuf;

fn test_dir(name: &str) -> PathBuf {
    let d = std::env::temp_dir().join(format!("kai-g2b-{name}-{}", std::process::id()));
    std::fs::create_dir_all(&d).unwrap();
    d
}

fn sample_txs() -> Vec<Tx> {
    vec![
        Tx::Set { key: "chain/name".into(), value: "a-townchain".into() },
        Tx::Set { key: "chain/id".into(), value: "658467".into() },
        Tx::Remove { key: "chain/name".into() },
        Tx::Set { key: "chain/name".into(), value: "a-townchain-v2".into() },
    ]
}

// ── AK: Crash-Recovery — Drop -> Reopen -> identischer Root ────────────

#[test]
fn crash_recovery_via_wal_replay() {
    let dir = test_dir("recovery");
    let state_path = dir.join("state.json");
    let wal_path = dir.join("wal.log");

    // Run 1: Tx-Log anwenden (WAL zuerst, durable), dann ABSTURZ
    let root_before = {
        let mut ps = PersistentState::open(&state_path, &wal_path).unwrap();
        for tx in sample_txs() {
            ps.apply(&tx).unwrap();
        }
        ps.store.state_root()
    };
    // Absturz: drop — nichts bleibt im Speicher
    drop(());

    // Run 2: Reopen von Disk — Recovery durch Replay
    let ps = PersistentState::open(&state_path, &wal_path).unwrap();
    assert_eq!(ps.store.state_root(), root_before, "Replay muss identischen Root ergeben");
    assert_eq!(ps.store.get("chain/id"), Some(&"658467".to_string()));
    assert_eq!(ps.store.get("chain/name"), Some(&"a-townchain-v2".to_string()));
    assert_eq!(ps.store.get("chain/removed"), None);
}

// ── AK: WAL allein — Append + Replay sind zueinander konsistent ─────────

#[test]
fn wal_append_then_replay_yields_all_txs() {
    let dir = test_dir("append-replay");
    let wal_path = dir.join("wal.log");
    let mut wal = WriteAheadLog::open(&wal_path).unwrap();
    for tx in sample_txs() {
        wal.append(&tx).unwrap();
    }
    let (txs, seq, _tip) = WriteAheadLog::replay(&wal_path).unwrap();
    assert_eq!(txs, sample_txs());
    assert_eq!(seq, 4);
}

// ── AK: Torn Tail — unvollständiger LETZTER Record wird verworfen ──────

#[test]
fn wal_torn_tail_discarded() {
    let dir = test_dir("torn-tail");
    let wal_path = dir.join("wal.log");
    let mut wal = WriteAheadLog::open(&wal_path).unwrap();
    for tx in sample_txs() {
        wal.append(&tx).unwrap();
    }
    // Absturz mitten im Schreiben simulieren: letzte Zeile abschneiden
    let content = std::fs::read_to_string(&wal_path).unwrap();
    let mut lines: Vec<&str> = content.lines().collect();
    lines.pop();
    let torn: String = lines.join("\n");
    std::fs::write(&wal_path, torn).unwrap();
    // Ein OEFFNEN nach dem Absturz: 3 gueltige Records, torn tail verworfen
    let reopened = WriteAheadLog::open(&wal_path).unwrap();
    assert_eq!(reopened.seq(), 3);
}

// ── AK: Corruption MITTEN im Log — fail-closed, kein Blind-Replay ─────

#[test]
fn wal_midfile_corruption_fail_closed() {
    let dir = test_dir("midfile");
    let wal_path = dir.join("wal.log");
    let mut wal = WriteAheadLog::open(&wal_path).unwrap();
    for tx in sample_txs() {
        wal.append(&tx).unwrap();
    }
    // Mittlere Zeile manipulieren (Seq-Nummer umbiegen)
    let content = std::fs::read_to_string(&wal_path).unwrap();
    let mut lines: Vec<String> = content.lines().map(|l| l.to_string()).collect();
    lines[1] = lines[1].replace("\"seq\":2", "\"seq\":99");
    std::fs::write(&wal_path, lines.join("\n")).unwrap();

    let result = WriteAheadLog::replay(&wal_path);
    assert!(matches!(result, Err(WalError::ChainBroken { .. })), "Corruption mid-file muss fail-closed sein");
}

// ── AK: Snapshot-Persistenz mit Tamper-Erkennung ────────────────────────

#[test]
fn snapshot_save_load_and_tamper_detection() {
    let dir = test_dir("snapshot");
    let path = dir.join("state.json");
    let mut store = StateStore::new();
    for tx in sample_txs() {
        store.apply(&tx);
    }
    save_snapshot_store(&store, 42, "tip-abc", &path).unwrap();

    // Roundtrip: identischer Root
    let loaded = load_snapshot_store(&path).unwrap();
    assert_eq!(loaded.state_root(), store.state_root());
    let (height, tip, root) = snapshot_meta(&path).unwrap();
    assert_eq!((height, tip.as_str()), (42, "tip-abc"));
    assert_eq!(root, store.state_root());

    // Manipulation: einen Eintrag in der Datei veraendern
    let raw = std::fs::read_to_string(&path).unwrap();
    let tampered = raw.replace("658467", "999999");
    std::fs::write(&path, tampered).unwrap();
    let result = load_snapshot_store(&path);
    assert!(result.is_err(), "manipuliertes Snapshot muss erkannt werden (load-verify)");
}

// ── AK: Checkpoint konsolidiert — danach Crash mit leerem WAL ──────────

#[test]
fn checkpoint_then_crash_recovers_from_snapshot() {
    let dir = test_dir("checkpoint");
    let state_path = dir.join("state.json");
    let wal_path = dir.join("wal.log");

    let root_before = {
        let mut ps = PersistentState::open(&state_path, &wal_path).unwrap();
        for tx in sample_txs() {
            ps.apply(&tx).unwrap();
        }
        ps.checkpoint(7, "tip-007", &state_path).unwrap();
        ps.store.state_root()
    };
    // WAL ist jetzt konsolidiert (leer); Absturz
    // Reopen: Snapshot wird geladen, leeres WAL replays nichts
    let mut ps = PersistentState::open(&state_path, &wal_path).unwrap();
    assert_eq!(ps.store.state_root(), root_before);
    // Und: weitere Txs nach dem Checkpoint landen im frischen WAL
    ps.apply(&Tx::Set { key: "post/ckpt".into(), value: "1".into() }).unwrap();
    drop(ps);
    let ps2 = PersistentState::open(&state_path, &wal_path).unwrap();
    assert_eq!(ps2.store.get("post/ckpt"), Some(&"1".to_string()));
}
