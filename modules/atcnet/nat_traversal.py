"""
ATCNet — NAT Traversal
STUN-based NAT detection and hole-punching for P2P connectivity.
Wiki: Kap. 22
"""
import socket
import struct
import threading
import logging
import time
from typing import Optional, Tuple

logger = logging.getLogger("atcnet.nat")

# Public STUN servers
STUN_SERVERS = [
    ("stun.l.google.com", 19302),
    ("stun1.l.google.com", 19302),
    ("stun.cloudflare.com", 3478),
]

STUN_MAGIC   = 0x2112A442
STUN_BINDING = 0x0001


class NATTraversal:
    """
    NAT Traversal via STUN (Session Traversal Utilities for NAT).
    Discovers external IP/port and attempts UDP hole-punching.
    """

    def __init__(self):
        self._external_ip: Optional[str] = None
        self._external_port: Optional[int] = None
        self._nat_type: str = "unknown"
        logger.info("NATTraversal initialized")

    def discover(self, timeout: float = 3.0) -> Tuple[Optional[str], Optional[int]]:
        """Discover external IP and port via STUN."""
        for server_host, server_port in STUN_SERVERS:
            try:
                result = self._stun_request(server_host, server_port, timeout)
                if result:
                    self._external_ip, self._external_port = result
                    logger.info(f"NAT: external {self._external_ip}:{self._external_port}")
                    return result
            except Exception as e:
                logger.debug(f"STUN {server_host} failed: {e}")
        logger.warning("NAT: all STUN servers failed")
        return None, None

    def _stun_request(self, host: str, port: int, timeout: float) -> Optional[Tuple[str, int]]:
        """Send STUN Binding Request and parse response."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        try:
            # Build STUN Binding Request
            transaction_id = b"\x00" * 12
            msg = struct.pack(">HHI", STUN_BINDING, 0, STUN_MAGIC) + transaction_id
            sock.sendto(msg, (host, port))
            data, _ = sock.recvfrom(2048)
            return self._parse_stun_response(data)
        finally:
            sock.close()

    def _parse_stun_response(self, data: bytes) -> Optional[Tuple[str, int]]:
        """Parse STUN response to extract mapped address."""
        if len(data) < 20:
            return None
        msg_type = struct.unpack(">H", data[0:2])[0]
        if msg_type != 0x0101:  # Binding Success Response
            return None
        # Parse attributes
        offset = 20
        while offset + 4 <= len(data):
            attr_type, attr_len = struct.unpack(">HH", data[offset:offset+4])
            offset += 4
            attr_data = data[offset:offset+attr_len]
            # XOR-MAPPED-ADDRESS (0x0020) or MAPPED-ADDRESS (0x0001)
            if attr_type in (0x0001, 0x0020) and len(attr_data) >= 8:
                family = struct.unpack(">H", attr_data[0:2])[0]
                if family == 0x0001:  # IPv4
                    port = struct.unpack(">H", attr_data[2:4])[0]
                    ip = socket.inet_ntoa(attr_data[4:8])
                    if attr_type == 0x0020:  # XOR
                        port ^= (STUN_MAGIC >> 16)
                        xor_bytes = struct.pack(">I", STUN_MAGIC)
                        ip_bytes = bytes(a ^ b for a, b in zip(attr_data[4:8], xor_bytes))
                        ip = socket.inet_ntoa(ip_bytes)
                    return ip, port
            offset += attr_len + (attr_len % 4 and 4 - attr_len % 4)
        return None

    def hole_punch(self, target_ip: str, target_port: int,
                   local_port: int = 9000, attempts: int = 5) -> bool:
        """UDP hole-punching to establish P2P connection behind NAT."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", local_port))
        sock.settimeout(1.0)
        ping = b"ATCNET_PUNCH"
        for i in range(attempts):
            try:
                sock.sendto(ping, (target_ip, target_port))
                data, addr = sock.recvfrom(64)
                if data == b"ATCNET_PUNCH_ACK":
                    logger.info(f"NAT hole-punch success: {target_ip}:{target_port}")
                    sock.close()
                    return True
            except socket.timeout:
                time.sleep(0.2)
        sock.close()
        logger.warning(f"NAT hole-punch failed: {target_ip}:{target_port}")
        return False

    def detect_nat_type(self) -> str:
        """Detect NAT type: open, full-cone, restricted, symmetric."""
        ip1, port1 = self.discover()
        if not ip1:
            self._nat_type = "blocked"
            return self._nat_type
        # Simple heuristic: compare local vs external
        local_ip = socket.gethostbyname(socket.gethostname())
        if ip1 == local_ip:
            self._nat_type = "open"
        else:
            self._nat_type = "nat"
        return self._nat_type

    @property
    def external_address(self) -> Tuple[Optional[str], Optional[int]]:
        return self._external_ip, self._external_port

    def status(self) -> dict:
        return {
            "external_ip": self._external_ip,
            "external_port": self._external_port,
            "nat_type": self._nat_type,
        }


_nat = NATTraversal()
def get_nat() -> NATTraversal:
    return _nat
