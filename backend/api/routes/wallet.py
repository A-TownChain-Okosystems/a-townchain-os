# backend/api/routes/wallet.py
# Wallet API Routes (via Gateway :5002)

from flask import Blueprint, jsonify, request

wallet_bp = Blueprint("wallet", __name__)
_wallet = None

def init_wallet(wallet_instance):
    global _wallet
    _wallet = wallet_instance

@wallet_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "wallet", "status": "online"})

@wallet_bp.route("/create", methods=["POST"])
def create():
    label = (request.json or {}).get("label", "default")
    return jsonify(_wallet.create_account(label))

@wallet_bp.route("/balance/<address>", methods=["GET"])
def balance(address):
    return jsonify(_wallet.get_balance(address))

@wallet_bp.route("/send", methods=["POST"])
def send():
    d = request.json or {}
    return jsonify(_wallet.send(d.get("from"), d.get("to"), float(d.get("amount", 0)), d.get("signature")))

@wallet_bp.route("/accounts", methods=["GET"])
def accounts():
    return jsonify({"accounts": _wallet.get_accounts()})

@wallet_bp.route("/nft/mint", methods=["POST"])
def mint_nft():
    d = request.json or {}
    return jsonify(_wallet.mint_nft(d.get("owner"), d.get("nft_id"), d.get("metadata", {})))

@wallet_bp.route("/nfts/<address>", methods=["GET"])
def nfts(address):
    return jsonify({"address": address, "nfts": _wallet.get_nfts(address)})
