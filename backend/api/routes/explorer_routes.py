"""
Blockchain Explorer API Routes — Issue #5
REST-Endpunkte für Block & TX Browser.
"""
from flask import Blueprint, jsonify, request
import time, hashlib

bp = Blueprint("explorer", __name__, url_prefix="/api/explorer")

# In-Memory Store (bis DB angebunden ist)
_blocks  = []
_txs     = {}

def _seed_demo_data():
    """Demo-Daten für Entwicklung."""
    if _blocks: return
    prev = "0"*64
    for i in range(20):
        block_hash = hashlib.sha256(f"{i}{prev}{time.time()}".encode()).hexdigest()
        txs = []
        for j in range(3):
            tx_hash = hashlib.sha256(f"tx-{i}-{j}".encode()).hexdigest()
            tx = {"hash": tx_hash, "from": f"ATC{'a'*8}{i:04x}",
                  "to": f"ATC{'b'*8}{j:04x}", "amount": (j+1)*10.5,
                  "fee": 0.001, "timestamp": time.time()-i*60, "status": "confirmed",
                  "block_height": i, "block_hash": block_hash}
            txs.append(tx); _txs[tx_hash] = tx
        _blocks.append({
            "height": i, "hash": block_hash, "prev_hash": prev,
            "timestamp": time.time() - i*60, "tx_count": len(txs),
            "transactions": txs, "miner": f"ATC{'c'*8}{i:04x}",
            "difficulty": 4, "nonce": i*1337, "size_bytes": 1024 + i*50,
        })
        prev = block_hash
    _blocks.reverse()

@bp.route("/blocks")
def blocks():
    _seed_demo_data()
    page  = int(request.args.get("page", 1))
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = (page-1)*limit
    data  = _blocks[offset:offset+limit]
    return jsonify({"blocks": data, "total": len(_blocks), "page": page, "limit": limit})

@bp.route("/blocks/<int:height>")
def block_by_height(height):
    _seed_demo_data()
    block = next((b for b in _blocks if b["height"]==height), None)
    if not block: return jsonify({"error": "Block not found"}), 404
    return jsonify(block)

@bp.route("/blocks/hash/<hash>")
def block_by_hash(hash):
    _seed_demo_data()
    block = next((b for b in _blocks if b["hash"]==hash), None)
    if not block: return jsonify({"error": "Block not found"}), 404
    return jsonify(block)

@bp.route("/tx/<hash>")
def tx_by_hash(hash):
    _seed_demo_data()
    tx = _txs.get(hash)
    if not tx: return jsonify({"error": "Transaction not found"}), 404
    return jsonify(tx)

@bp.route("/address/<address>")
def address_txs(address):
    _seed_demo_data()
    txs = [t for t in _txs.values() if t["from"]==address or t["to"]==address]
    balance = sum(t["amount"] for t in txs if t["to"]==address) - sum(t["amount"] for t in txs if t["from"]==address)
    return jsonify({"address": address, "balance": round(balance, 6), "tx_count": len(txs), "transactions": txs[:50]})

@bp.route("/search")
def search():
    q = request.args.get("q","").strip()
    if not q: return jsonify({"error": "Query required"}), 400
    _seed_demo_data()
    # TX-Hash?
    if q in _txs: return jsonify({"type": "tx", "data": _txs[q]})
    # Block-Hash?
    block = next((b for b in _blocks if b["hash"]==q), None)
    if block: return jsonify({"type": "block", "data": block})
    # Höhe?
    try:
        block = next((b for b in _blocks if b["height"]==int(q)), None)
        if block: return jsonify({"type": "block", "data": block})
    except: pass
    return jsonify({"type": "not_found"}), 404

@bp.route("/stats")
def stats():
    _seed_demo_data()
    return jsonify({
        "block_height": len(_blocks),
        "total_txs":    len(_txs),
        "avg_block_time": 12.5,
        "tps":          round(len(_txs)/max(1,len(_blocks)*12.5),2),
        "active_nodes": 7,
    })
