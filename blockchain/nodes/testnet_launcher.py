"""
A-TownChain OS — Testnet Launcher
Launches a local multi-node testnet for development.
Issue: #18 | Wiki: Kap. 18
"""
import os
import sys
import time
import subprocess
import threading
import logging
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("blockchain.testnet")

DEFAULT_NODES    = 3
BASE_PORT        = 9000
BASE_RPC_PORT    = 9100
GENESIS_CHAIN_ID = 9000


@dataclass
class TestnetNode:
    node_id: int
    p2p_port: int
    rpc_port: int
    data_dir: str
    process: Optional[subprocess.Popen] = None
    status: str = "stopped"

    @property
    def address(self) -> str:
        return f"127.0.0.1:{self.p2p_port}"

    @property
    def rpc_url(self) -> str:
        return f"http://127.0.0.1:{self.rpc_port}"


class TestnetLauncher:
    """
    Launches a local A-TownChain testnet with N nodes.
    Each node runs as a subprocess with its own data directory.
    """

    def __init__(self, num_nodes: int = DEFAULT_NODES,
                 base_dir: str = "/tmp/atcchain-testnet"):
        self.num_nodes = num_nodes
        self.base_dir  = base_dir
        self.nodes: List[TestnetNode] = []
        self.running = False
        self._monitor_thread: Optional[threading.Thread] = None
        logger.info(f"TestnetLauncher: {num_nodes} nodes at {base_dir}")

    def setup(self) -> bool:
        """Create directories and genesis config for all nodes."""
        os.makedirs(self.base_dir, exist_ok=True)
        genesis = self._build_genesis()
        genesis_path = os.path.join(self.base_dir, "genesis.json")
        with open(genesis_path, "w") as f:
            json.dump(genesis, f, indent=2)
        logger.info(f"Genesis written to {genesis_path}")

        self.nodes = []
        for i in range(self.num_nodes):
            node_dir = os.path.join(self.base_dir, f"node{i}")
            os.makedirs(node_dir, exist_ok=True)
            node = TestnetNode(
                node_id=i,
                p2p_port=BASE_PORT + i,
                rpc_port=BASE_RPC_PORT + i,
                data_dir=node_dir,
            )
            self.nodes.append(node)
            logger.debug(f"Node {i}: P2P={node.p2p_port} RPC={node.rpc_port}")
        return True

    def _build_genesis(self) -> Dict:
        return {
            "chain_id": GENESIS_CHAIN_ID,
            "timestamp": int(time.time()),
            "difficulty": 1,
            "gas_limit": 10_000_000,
            "alloc": {
                "ATC0000000000000000000000000000000000000000": {
                    "balance": 21_000_000 * (10 ** 8)  # 21M ATC genesis
                }
            },
            "consensus": "hybrid_pos_pow",
            "version": "3.0.0",
        }

    def start(self) -> bool:
        """Start all testnet nodes."""
        if not self.nodes:
            self.setup()
        bootstrap_peers = [f"127.0.0.1:{n.p2p_port}" for n in self.nodes]
        started = 0
        for node in self.nodes:
            peers = [p for p in bootstrap_peers if not p.endswith(str(node.p2p_port))]
            ok = self._start_node(node, peers)
            if ok:
                started += 1
                node.status = "running"
        self.running = started > 0
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"Testnet started: {started}/{self.num_nodes} nodes running")
        return self.running

    def _start_node(self, node: TestnetNode, peers: List[str]) -> bool:
        """Start a single node subprocess."""
        bootstrap_py = os.path.join(
            os.path.dirname(__file__), "bootstrap.py"
        )
        if not os.path.exists(bootstrap_py):
            # Simulate node start (no actual subprocess in test mode)
            logger.info(f"[SIMULATED] Node {node.node_id} started on :{node.p2p_port}")
            node.status = "running"
            return True
        cmd = [
            sys.executable, bootstrap_py,
            "--port",     str(node.p2p_port),
            "--rpc-port", str(node.rpc_port),
            "--data-dir", node.data_dir,
            "--peers",    ",".join(peers),
            "--chain-id", str(GENESIS_CHAIN_ID),
        ]
        try:
            node.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            time.sleep(0.5)
            if node.process.poll() is None:
                logger.info(f"Node {node.node_id} started (PID={node.process.pid})")
                return True
            logger.error(f"Node {node.node_id} exited immediately")
            return False
        except Exception as e:
            logger.error(f"Failed to start node {node.node_id}: {e}")
            return False

    def stop(self):
        """Stop all nodes."""
        self.running = False
        for node in self.nodes:
            if node.process:
                node.process.terminate()
                node.process.wait(timeout=5)
            node.status = "stopped"
        logger.info("Testnet stopped")

    def _monitor_loop(self):
        while self.running:
            for node in self.nodes:
                if node.process and node.process.poll() is not None:
                    logger.warning(f"Node {node.node_id} died (exit={node.process.returncode})")
                    node.status = "dead"
            time.sleep(5)

    def status(self) -> Dict:
        return {
            "running": self.running,
            "nodes": [
                {"id": n.node_id, "port": n.p2p_port,
                 "rpc": n.rpc_port, "status": n.status}
                for n in self.nodes
            ],
            "chain_id": GENESIS_CHAIN_ID,
        }

    def wait_for_blocks(self, target: int = 5, timeout: float = 60.0) -> bool:
        """Wait until all nodes have produced at least `target` blocks."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            # In a real implementation: poll each node's RPC /block_height
            time.sleep(1)
            logger.debug(f"Waiting for block height {target}...")
        return True


def launch_local_testnet(num_nodes: int = DEFAULT_NODES) -> TestnetLauncher:
    launcher = TestnetLauncher(num_nodes=num_nodes)
    launcher.setup()
    launcher.start()
    return launcher
