// frontend/assets/js/api.js
// A-TownChain API Client
//
// ARCHITEKTUR:
//   Frontend → API Gateway (Port 4000) → Backend Services
//   Frontend spricht NIEMALS direkt mit dem Backend!

const GATEWAY = "http://localhost:4000/api";
const API_KEY  = "atc-dev-key-2025";  // aus .env laden in Production

const headers = {
  "Content-Type":  "application/json",
  "X-API-Key":     API_KEY
};

const ATC_API = {

  // ── System ─────────────────────────────────────────
  async getStatus() {
    return await _get("status");
  },

  async getGatewayHealth() {
    const res = await fetch("http://localhost:4000/gateway/health", { headers });
    return await res.json();
  },

  // ── Blockchain ─────────────────────────────────────
  async getBlockchainInfo() {
    return await _get("blockchain/info");
  },

  async getBlock(height) {
    return await _get(`blockchain/blocks/${height}`);
  },

  // ── Wallet ─────────────────────────────────────────
  async getBalance(address) {
    return await _get(`wallet/balance/${address}`);
  },

  async sendTransfer(from, to, amount) {
    return await _post("wallet/send", { from, to, amount });
  },

  // ── AI ─────────────────────────────────────────────
  async queryAI(prompt) {
    return await _post("ai/query", { prompt });
  },

  // ── Game ───────────────────────────────────────────
  async getShivamon(id) {
    return await _get(`game/shivamon/${id}`);
  }
};

// ── Interne Hilfsfunktionen ─────────────────────────
async function _get(endpoint) {
  try {
    const res = await fetch(`${GATEWAY}/${endpoint}`, { headers });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.error(`[ATC API] GET /${endpoint} failed:`, e.message);
    return { error: e.message, offline: true };
  }
}

async function _post(endpoint, body) {
  try {
    const res = await fetch(`${GATEWAY}/${endpoint}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.error(`[ATC API] POST /${endpoint} failed:`, e.message);
    return { error: e.message, offline: true };
  }
}

// ── Backend-Status im Dashboard anzeigen ───────────
window.addEventListener("DOMContentLoaded", async () => {
  const health = await ATC_API.getGatewayHealth();
  const el = document.getElementById("backend-status");
  if (el) {
    const online = health.gateway === "online";
    el.textContent = online ? "● GATEWAY ONLINE" : "● GATEWAY OFFLINE";
    el.style.color  = online ? "#00ffb3" : "#ff2d78";
  }
});
