"""
Node Monitoring Dashboard — Issue #19
Echtzeit-Monitoring für das A-TownChain Testnet.
Flask-basiertes Dashboard mit Prometheus-Metriken.
"""
import time, json, threading, urllib.request
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Node-Konfiguration
NODES = [
    {"id": "bootstrap-01", "url": "http://localhost:5010", "role": "bootstrap"},
    {"id": "validator-01", "url": "http://localhost:5011", "role": "validator"},
    {"id": "validator-02", "url": "http://localhost:5012", "role": "validator"},
    {"id": "fullnode-01",  "url": "http://localhost:5013", "role": "full"},
    {"id": "gateway-01",   "url": "http://localhost:5014", "role": "gateway"},
]

_cache = {"nodes": [], "updated": 0, "chain": {}}
_lock  = threading.Lock()

def _probe_node(node):
    """Einzelnen Node abfragen."""
    result = {**node, "status": "offline", "height": 0, "peers": 0,
              "tps": 0.0, "latency_ms": 0}
    try:
        start = time.time()
        req   = urllib.request.Request(f"{node['url']}/health", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=2) as r:
            data = json.loads(r.read())
            result["status"]     = "online"
            result["height"]     = data.get("block_height", 0)
            result["peers"]      = data.get("peer_count", 0)
            result["tps"]        = data.get("tps", 0.0)
            result["latency_ms"] = round((time.time() - start) * 1000, 1)
    except Exception:
        pass
    return result

def _refresh():
    """Alle Nodes parallel abfragen."""
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        results = list(ex.map(_probe_node, NODES))
    with _lock:
        _cache["nodes"]   = results
        _cache["updated"] = time.time()
        online = [n for n in results if n["status"] == "online"]
        _cache["chain"] = {
            "online_nodes": len(online),
            "total_nodes":  len(NODES),
            "best_height":  max((n["height"] for n in online), default=0),
            "avg_latency":  round(sum(n["latency_ms"] for n in online) / max(len(online),1), 1),
            "total_tps":    round(sum(n["tps"] for n in online), 2),
        }

# Background-Refresh alle 10s
def _bg():
    while True:
        try: _refresh()
        except: pass
        time.sleep(10)
threading.Thread(target=_bg, daemon=True).start()

@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route("/api/nodes")
def api_nodes():
    with _lock:
        return jsonify(_cache)

@app.route("/api/nodes/refresh")
def api_refresh():
    _refresh()
    with _lock:
        return jsonify(_cache)

@app.route("/metrics")
def prometheus_metrics():
    """Prometheus-kompatibler /metrics Endpunkt."""
    with _lock:
        nodes = _cache["nodes"]
        chain = _cache["chain"]
    lines = [
        "# HELP atc_nodes_online Anzahl Online-Nodes",
        "# TYPE atc_nodes_online gauge",
        f"atc_nodes_online {chain.get('online_nodes',0)}",
        "# HELP atc_best_block_height Höchste bekannte Block-Höhe",
        "# TYPE atc_best_block_height gauge",
        f"atc_best_block_height {chain.get('best_height',0)}",
        "# HELP atc_tps Transaktionen pro Sekunde (gesamt)",
        "# TYPE atc_tps gauge",
        f"atc_tps {chain.get('total_tps',0)}",
    ]
    for n in nodes:
        nid = n["id"].replace("-","_")
        lines += [
            f'atc_node_up{{node="{n["id"]}",role="{n["role"]}"}} {1 if n["status"]=="online" else 0}',
            f'atc_node_height{{node="{n["id"]}"}} {n["height"]}',
            f'atc_node_latency_ms{{node="{n["id"]}"}} {n["latency_ms"]}',
        ]
    return "\n".join(lines), 200, {"Content-Type": "text/plain"}

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="10">
<title>A-TownChain Testnet Monitor</title>
<style>
  :root{--bg:#0a0a1a;--panel:#111128;--border:#2a2a5a;--neon:#00f5ff;--green:#00ff88;--red:#ff4444;--text:#e0e0ff;--dim:#6060a0}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:"Courier New",monospace;padding:24px}
  h1{color:var(--neon);text-shadow:0 0 12px var(--neon);margin-bottom:20px;font-size:1.4em}
  .chain-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:24px}
  .stat{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:16px;text-align:center}
  .stat .val{font-size:2em;font-weight:bold;color:var(--neon)}
  .stat .lbl{font-size:0.75em;color:var(--dim);margin-top:4px}
  .nodes{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
  .node{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:16px}
  .node.online{border-color:var(--green)}
  .node.offline{border-color:var(--red);opacity:0.7}
  .node-name{font-weight:bold;margin-bottom:8px}
  .node-role{font-size:0.75em;color:var(--dim);margin-bottom:12px}
  .metric{display:flex;justify-content:space-between;font-size:0.85em;padding:3px 0;border-bottom:1px solid #1a1a3a}
  .metric .val{color:var(--neon)}
  .badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:0.75em;font-weight:bold}
  .badge.online{background:#00ff8820;color:var(--green)}
  .badge.offline{background:#ff444420;color:var(--red)}
  .updated{color:var(--dim);font-size:0.8em;margin-top:16px;text-align:right}
</style>
</head>
<body>
<h1>🔗 A-TownChain OS — Testnet Monitor</h1>
<div class="chain-stats" id="chain-stats">Lade...</div>
<div class="nodes" id="nodes">Lade...</div>
<div class="updated" id="updated"></div>
<script>
async function load(){
  const r = await fetch('/api/nodes');
  const d = await r.json();
  const c = d.chain||{};
  document.getElementById('chain-stats').innerHTML = [
    {val:c.online_nodes+'/'+c.total_nodes, lbl:'Nodes Online'},
    {val:c.best_height, lbl:'Block-Höhe'},
    {val:c.total_tps+' TPS', lbl:'Durchsatz'},
    {val:c.avg_latency+' ms', lbl:'Ø Latenz'},
  ].map(s=>`<div class="stat"><div class="val">${s.val}</div><div class="lbl">${s.lbl}</div></div>`).join('');
  document.getElementById('nodes').innerHTML = (d.nodes||[]).map(n=>`
    <div class="node ${n.status}">
      <div class="node-name">${n.id} <span class="badge ${n.status}">${n.status}</span></div>
      <div class="node-role">${n.role.toUpperCase()}</div>
      <div class="metric"><span>Block-Höhe</span><span class="val">${n.height}</span></div>
      <div class="metric"><span>Peers</span><span class="val">${n.peers}</span></div>
      <div class="metric"><span>TPS</span><span class="val">${n.tps}</span></div>
      <div class="metric"><span>Latenz</span><span class="val">${n.latency_ms} ms</span></div>
    </div>`).join('');
  document.getElementById('updated').textContent = 'Aktualisiert: '+new Date().toLocaleTimeString();
}
load(); setInterval(load, 10000);
</script>
</body>
</html>"""

if __name__ == "__main__":
    _refresh()
    print("🖥️  Monitor läuft auf http://localhost:9090")
    print("📊 Prometheus: http://localhost:9090/metrics")
    app.run(host="0.0.0.0", port=9090, debug=False)
