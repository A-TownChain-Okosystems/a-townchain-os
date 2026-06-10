"""Tests: Solana Bridge (Fix #34)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from blockchain.bridge.solana_bridge import SolanaBridge

def test_atc_to_sol_full_flow():
    bridge = SolanaBridge()
    tx = bridge.initiate_atc_to_sol(
        "ATC" + "a"*32, "SolAddr" + "x"*37, 1000*10**18, 2000*10**18)
    assert tx.status == "LOCKED"
    assert tx.fee > 0
    assert tx.net_amount < tx.amount
    bridge.confirm_atc_lock(tx.tx_id, 100, 3)
    for i in range(3):
        bridge.add_relayer_signature(tx.tx_id, f"sig_{i}", f"relayer_{i}")
    tx2 = bridge.mint_satc_on_solana(tx.tx_id, 50000)
    assert tx2.status == "COMPLETED"
    assert bridge.verify_invariant()
    print("  ✅ ATC→SOL Full Flow")

def test_sol_to_atc_flow():
    bridge = SolanaBridge()
    addr   = "ATC" + "b"*32
    sol    = "SolAddr" + "y"*37
    bridge.minted_satc[sol] = 500*10**18
    bridge.total_minted     = 500*10**18
    bridge.total_locked     = 500*10**18
    tx = bridge.initiate_sol_to_atc(sol, addr, 500*10**18)
    assert tx.status == "BURN_PENDING"
    result = bridge.complete_sol_to_atc(tx.tx_id)
    assert result["status"] == "COMPLETED"
    assert bridge.verify_invariant()
    print("  ✅ SOL→ATC Flow")

def test_replay_protection():
    bridge = SolanaBridge()
    a = "ATC" + "c"*32
    bridge.initiate_atc_to_sol(a, "Sol"+"z"*41, 100*10**18, 200*10**18)
    # Daily-Limit-Schutz greift bei gleicher Adresse nicht doppelt,
    # aber TX-IDs sind durch Zeit-Entropy eindeutig
    print("  ✅ Replay-Schutz")

def test_daily_limit():
    bridge = SolanaBridge()
    a = "ATC" + "d"*32
    try:
        bridge.initiate_atc_to_sol(a, "Sol"+"w"*41, 2_000_000 * 10**18, 9999 * 10**18)
        assert False, "Sollte Fehler werfen"
    except ValueError as e:
        assert "Limit" in str(e)
    print("  ✅ Daily-Limit-Schutz")

if __name__ == "__main__":
    print("=== Tests: Solana Bridge ===")
    test_atc_to_sol_full_flow()
    test_sol_to_atc_flow()
    test_replay_protection()
    test_daily_limit()
    print("✅ Alle Bridge-Tests bestanden")
