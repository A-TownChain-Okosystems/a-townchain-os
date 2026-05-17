# backend/api/server.py
# REST API — verbindet Core mit Frontend

from flask import Flask, jsonify, request
from flask_cors import CORS

def create_app(kernel=None):
    app = Flask(__name__)
    CORS(app)  # erlaubt Frontend-Anfragen

    @app.route("/api/status", methods=["GET"])
    def status():
        return jsonify({
            "status": "online",
            "version": "2.0",
            "chain": "A-TownChain",
            "kernel": kernel.running if kernel else False
        })

    @app.route("/api/modules", methods=["GET"])
    def modules():
        mods = [m.__class__.__name__ for m in kernel.loader.modules] if kernel else []
        return jsonify({"modules": mods})

    @app.route("/api/transfer", methods=["POST"])
    def transfer():
        data = request.json
        if kernel:
            kernel.event_bus.emit("transfer", data)
        return jsonify({"success": True, "tx": data})

    @app.route("/api/blockchain/info", methods=["GET"])
    def blockchain_info():
        return jsonify({
            "chain": "A-TownChain",
            "consensus": "PoI+PoS",
            "blocks": 48291,
            "tps": 4200,
            "nodes": 128
        })

    @app.route("/api/ai/query", methods=["POST"])
    def ai_query():
        prompt = request.json.get("prompt", "")
        # Gemini API wird hier angebunden
        return jsonify({
            "response": f"[AI] Verarbeite: {prompt}",
            "model": "gemini-2.0",
            "tokens": len(prompt.split())
        })

    return app
