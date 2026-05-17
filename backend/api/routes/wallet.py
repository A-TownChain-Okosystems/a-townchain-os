# backend/api/routes/wallet.py
# Wallet API Routes — ATC Token

from flask import Blueprint, jsonify, request

wallet_bp = Blueprint("wallet", __name__)

@wallet_bp.route("/balance/<address>", methods=["GET"])
def balance(address):
    return jsonify({"address": address, "balance": 0, "token": "ATC"})

@wallet_bp.route("/send", methods=["POST"])
def send():
    data = request.json
    return jsonify({"success": True, "from": data.get("from"), "to": data.get("to"), "amount": data.get("amount")})
