// frontend/assets/js/api.js
// API Client — verbindet Frontend mit Backend

const API_BASE = "http://localhost:5000/api";

const ATC_API = {
  async getStatus() {
    try {
      const res = await fetch(`${API_BASE}/status`);
      return await res.json();
    } catch {
      return { status: "offline" };
    }
  },

  async getBlockchainInfo() {
    try {
      const res = await fetch(`${API_BASE}/blockchain/info`);
      return await res.json();
    } catch {
      return null;
    }
  },

  async sendTransfer(from, to, amount) {
    const res = await fetch(`${API_BASE}/transfer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ from, to, amount })
    });
    return await res.json();
  },

  async queryAI(prompt) {
    const res = await fetch(`${API_BASE}/ai/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });
    return await res.json();
  }
};

// Auto-ping backend on load
window.addEventListener("DOMContentLoaded", async () => {
  const status = await ATC_API.getStatus();
  const el = document.getElementById("backend-status");
  if (el) {
    el.textContent = status.status === "online" ? "● ONLINE" : "● OFFLINE";
    el.style.color = status.status === "online" ? "#00ffb3" : "#ff2d78";
  }
  console.log("[ATC] Backend:", status);
});
