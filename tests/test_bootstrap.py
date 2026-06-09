"""
Tests für Bootstrap Node (Issue #14 — ATN-1000)
"""
import sys, os, json, socket, threading, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_bootstrap_import():
    from blockchain.nodes.bootstrap import BootstrapNode
    node = BootstrapNode(host="127.0.0.1", port=19001, node_id="test-node-001")
    assert node.node_id == "test-node-001"
    assert node.port == 19001
    print("  ✅ BootstrapNode importierbar")

def test_bootstrap_peer_registry():
    from blockchain.nodes.bootstrap import BootstrapNode
    node = BootstrapNode(host="127.0.0.1", port=19002, node_id="test-node-002")
    # Peer direkt registrieren (ohne UDP)
    node.peers["peer-001"] = {"node_id":"peer-001","host":"127.0.0.1","port":4002,"last_seen":time.time()}
    assert "peer-001" in node.peers
    print("  ✅ Peer-Registry funktioniert")

def test_bootstrap_peer_expiry():
    from blockchain.nodes.bootstrap import BootstrapNode
    node = BootstrapNode(host="127.0.0.1", port=19003, node_id="test-node-003")
    # Alten Peer eintragen (30min alt → soll entfernt werden)
    node.peers["old-peer"] = {"node_id":"old-peer","host":"127.0.0.1","port":4003,"last_seen": time.time()-2000}
    node.peers["new-peer"] = {"node_id":"new-peer","host":"127.0.0.1","port":4004,"last_seen": time.time()}
    node._cleanup_stale_peers(max_age=1800)
    assert "old-peer" not in node.peers
    assert "new-peer" in node.peers
    print("  ✅ Stale Peer Cleanup funktioniert")

def test_bootstrap_message_handling():
    from blockchain.nodes.bootstrap import BootstrapNode
    node = BootstrapNode(host="127.0.0.1", port=19004, node_id="test-node-004")
    # Announce-Nachricht simulieren
    announce_msg = json.dumps({
        "type": "ANNOUNCE", "node_id": "peer-X",
        "host": "127.0.0.1", "port": 5000,
        "capabilities": ["relay"]
    }).encode()
    response = node._handle_message(announce_msg, ("127.0.0.1", 5000))
    resp = json.loads(response)
    assert resp["type"] == "PEER_LIST"
    assert "peer-X" in node.peers
    print("  ✅ ANNOUNCE → PEER_LIST funktioniert")

def test_bootstrap_ping_pong():
    from blockchain.nodes.bootstrap import BootstrapNode
    node = BootstrapNode(host="127.0.0.1", port=19005, node_id="test-node-005")
    ping_msg = json.dumps({"type": "PING", "node_id": "pinger-1"}).encode()
    response = node._handle_message(ping_msg, ("127.0.0.1", 6000))
    resp = json.loads(response)
    assert resp["type"] == "PONG"
    print("  ✅ PING → PONG funktioniert")

def test_bootstrap_get_peers():
    from blockchain.nodes.bootstrap import BootstrapNode
    node = BootstrapNode(host="127.0.0.1", port=19006, node_id="test-node-006")
    for i in range(5):
        node.peers[f"p-{i}"] = {"node_id":f"p-{i}","host":"127.0.0.1","port":4000+i,"last_seen":time.time()}
    msg = json.dumps({"type": "GET_PEERS", "limit": 3}).encode()
    response = node._handle_message(msg, ("127.0.0.1", 7000))
    resp = json.loads(response)
    assert resp["type"] == "PEER_LIST"
    assert len(resp["peers"]) <= 3
    print("  ✅ GET_PEERS mit Limit funktioniert")

if __name__ == "__main__":
    tests = [v for k,v in list(globals().items()) if k.startswith("test_")]
    ok = fail = 0
    for t in tests:
        try: t(); ok += 1
        except Exception as e: print(f"  ❌ {t.__name__}: {e}"); fail += 1
    print(f"\n{ok}/{ok+fail} Tests bestanden")
    sys.exit(0 if fail == 0 else 1)
