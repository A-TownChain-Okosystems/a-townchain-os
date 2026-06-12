"""
A-TownChain OS — Grafana Dashboard Exporter
Generates Grafana dashboard JSON and syncs metrics.
Issue: #44 | Wiki: Kap. 49
"""
import json
import time
import logging
import requests
from typing import Dict, List, Optional
from monitoring.prometheus_metrics import get_registry

logger = logging.getLogger("monitoring.grafana")

GRAFANA_URL  = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "atcchain"


def build_dashboard() -> Dict:
    """Generate Grafana dashboard JSON for A-TownChain OS."""
    panels = []

    def stat_panel(pid, title, expr, unit="short", x=0, y=0, w=6, h=4):
        return {
            "id": pid, "type": "stat", "title": title,
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [{"expr": expr, "refId": "A"}],
            "fieldConfig": {"defaults": {"unit": unit, "thresholds": {
                "steps": [{"color": "green", "value": 0},
                           {"color": "yellow", "value": 100},
                           {"color": "red", "value": 1000}]
            }}},
        }

    def graph_panel(pid, title, metrics, x=0, y=4, w=12, h=8):
        return {
            "id": pid, "type": "timeseries", "title": title,
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [{"expr": m, "refId": chr(65+i)} for i, m in enumerate(metrics)],
        }

    # Row 1: Key Stats
    panels += [
        stat_panel(1,  "Block Height",    "atc_block_height",       "none",   0, 0, 6, 4),
        stat_panel(2,  "Block Time (s)",  "atc_block_time_seconds", "s",      6, 0, 6, 4),
        stat_panel(3,  "TPS",             "atc_tps",                "reqps", 12, 0, 6, 4),
        stat_panel(4,  "Peer Count",      "atc_peer_count",         "none",  18, 0, 6, 4),
    ]
    # Row 2: Graphs
    panels += [
        graph_panel(5,  "Block Height over Time", ["atc_block_height"],         0,  4, 12, 8),
        graph_panel(6,  "TPS over Time",           ["atc_tps"],                12,  4, 12, 8),
        graph_panel(7,  "API Requests",    ["atc_api_requests_total"],          0, 12, 12, 8),
        graph_panel(8,  "IPC Messages",    ["atc_ipc_messages_total"],         12, 12, 12, 8),
    ]
    # Row 3: Infrastructure
    panels += [
        stat_panel(9,  "Validators",      "atc_validator_count",  "none", 0, 20, 6, 4),
        stat_panel(10, "Mempool Size",    "atc_mempool_size",     "none", 6, 20, 6, 4),
        stat_panel(11, "Total TX",        "atc_tx_total",         "none",12, 20, 6, 4),
        stat_panel(12, "AI Queries",      "atc_ai_queries_total", "none",18, 20, 6, 4),
    ]

    return {
        "dashboard": {
            "id": None,
            "uid": "atcchain-main",
            "title": "A-TownChain OS — Main Dashboard",
            "tags": ["atcchain", "blockchain", "kaios"],
            "timezone": "browser",
            "schemaVersion": 38,
            "version": 1,
            "refresh": "10s",
            "time": {"from": "now-1h", "to": "now"},
            "panels": panels,
        },
        "folderId": 0,
        "overwrite": True,
    }


def export_to_file(path: str = "monitoring/grafana_dashboard.json"):
    """Export dashboard to local JSON file."""
    dash = build_dashboard()
    with open(path, "w") as f:
        json.dump(dash, f, indent=2)
    logger.info(f"Grafana dashboard exported to {path}")
    return path


def push_to_grafana(grafana_url: str = GRAFANA_URL,
                    user: str = GRAFANA_USER,
                    password: str = GRAFANA_PASS) -> bool:
    """Push dashboard to running Grafana instance."""
    dash = build_dashboard()
    try:
        r = requests.post(
            f"{grafana_url}/api/dashboards/db",
            auth=(user, password),
            headers={"Content-Type": "application/json"},
            json=dash,
            timeout=10,
        )
        if r.status_code in (200, 201):
            logger.info("Grafana dashboard pushed successfully")
            return True
        logger.warning(f"Grafana push failed: {r.status_code} {r.text[:100]}")
        return False
    except Exception as e:
        logger.error(f"Grafana push error: {e}")
        return False


def update_metrics_from_node(node_data: Dict):
    """Update Prometheus metrics from node state dict."""
    reg = get_registry()
    reg.set("atc_block_height",       node_data.get("block_height", 0))
    reg.set("atc_block_time_seconds", node_data.get("block_time", 0))
    reg.set("atc_mempool_size",       node_data.get("mempool_size", 0))
    reg.set("atc_peer_count",         node_data.get("peer_count", 0))
    reg.set("atc_tps",                node_data.get("tps", 0))
    reg.set("atc_validator_count",    node_data.get("validators", 0))
    reg.inc("atc_block_total",        node_data.get("new_blocks", 0))
    reg.inc("atc_tx_total",           node_data.get("new_txs", 0))
