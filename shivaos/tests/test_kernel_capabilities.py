"""Integrationstests: Capability-Durchsetzung im echten ShivaKernel.
Verifiziert vor Push: alloc()/create_channel() vergeben Capabilities,
read_memory/write_memory/send_with_capability/recv_with_capability
setzen sie tatsaechlich durch."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from shivaos.kernel.kernel import ShivaKernel, ProcessType
from shivaos.kernel.capabilities import CapabilityError


@pytest.fixture
def kernel():
    k = ShivaKernel()
    pid = k._spawn_system("test_proc", ProcessType.SERVICE)
    return k, pid


def test_alloc_grants_capability(kernel):
    k, pid = kernel
    region = k.alloc(1024, pid)
    assert hasattr(region, "_cap_id")
    caps = k.capabilities.capabilities_for_pid(pid)
    assert any(c.cap_id == region._cap_id for c in caps)


def test_read_write_memory_with_valid_capability(kernel):
    k, pid = kernel
    region = k.alloc(1024, pid)
    k.write_memory(region._cap_id, region, 0, b"hello")
    assert k.read_memory(region._cap_id, region, 0, 5) == b"hello"


def test_read_memory_denied_without_capability(kernel):
    k, pid = kernel
    region = k.alloc(1024, pid)
    with pytest.raises(CapabilityError):
        k.read_memory("invalid-cap", region, 0, 5)


def test_free_revokes_capability(kernel):
    k, pid = kernel
    region = k.alloc(1024, pid)
    cap_id = region._cap_id
    k.free(region)
    with pytest.raises(CapabilityError):
        k.read_memory(cap_id, region, 0, 1)


def test_create_channel_grants_capability(kernel):
    k, pid = kernel
    cid = k.create_channel(sender_pid=pid)
    caps = [c for c in k.capabilities.capabilities_for_pid(pid) if c.resource_type == "ipc_channel"]
    assert len(caps) == 1
    assert caps[0].resource_id == cid


def test_send_recv_with_valid_capability(kernel):
    k, pid = kernel
    cid = k.create_channel(sender_pid=pid)
    cap = [c for c in k.capabilities.capabilities_for_pid(pid) if c.resource_type == "ipc_channel"][0]

    assert k.send_with_capability(cap.cap_id, cid, pid, "test", {"x": 1})
    msg = k.recv_with_capability(cap.cap_id, cid, pid)
    assert msg.data == {"x": 1}


def test_send_denied_without_capability(kernel):
    k, pid = kernel
    cid = k.create_channel(sender_pid=pid)
    with pytest.raises(CapabilityError):
        k.send_with_capability("invalid-cap", cid, pid, "test", {})
