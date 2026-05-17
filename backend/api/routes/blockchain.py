# backend/api/routes/blockchain.py
# Blockchain API Routes

from flask import Blueprint, jsonify

blockchain_bp = Blueprint("blockchain", __name__)

@blockchain_bp.route("/blocks", methods=["GET"])
def get_blocks():
    return jsonify({"blocks": [], "total": 48291})

@blockchain_bp.route("/tx/<tx_id>", methods=["GET"])
def get_tx(tx_id):
    return jsonify({"tx_id": tx_id, "status": "confirmed", "chain": "A-TownChain"})
