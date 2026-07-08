"""Unit-Tests fuer das Capability-System. Reine Logik, keine Kernel-Instanz noetig."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from shivaos.kernel.capabilities import (
    CapabilityManager, Right, ResourceType, CapabilityError
)


def test_grant_and_check_basic():
    mgr = CapabilityManager()
    cap = mgr.grant(owner_pid=1, resource_type=ResourceType.MEMORY,
                    resource_id=42, rights=Right.READ | Right.WRITE)
    assert mgr.check(cap.cap_id, ResourceType.MEMORY, 42, Right.READ)
    assert mgr.check(cap.cap_id, ResourceType.MEMORY, 42, Right.WRITE)
    assert not mgr.check(cap.cap_id, ResourceType.MEMORY, 42, Right.EXECUTE)


def test_check_wrong_resource_fails():
    mgr = CapabilityManager()
    cap = mgr.grant(owner_pid=1, resource_type=ResourceType.MEMORY,
                    resource_id=42, rights=Right.ALL)
    assert not mgr.check(cap.cap_id, ResourceType.MEMORY, 99, Right.READ)
    assert not mgr.check(cap.cap_id, ResourceType.IPC_CHANNEL, 42, Right.READ)


def test_require_raises_on_denial():
    mgr = CapabilityManager()
    cap = mgr.grant(owner_pid=1, resource_type=ResourceType.MEMORY,
                    resource_id=1, rights=Right.READ)
    with pytest.raises(CapabilityError):
        mgr.require(cap.cap_id, ResourceType.MEMORY, 1, Right.WRITE)
    mgr.require(cap.cap_id, ResourceType.MEMORY, 1, Right.READ)  # darf nicht werfen


def test_unknown_capability_denied():
    mgr = CapabilityManager()
    assert not mgr.check("does-not-exist", ResourceType.MEMORY, 1, Right.READ)


def test_delegate_narrows_rights():
    mgr = CapabilityManager()
    parent = mgr.grant(owner_pid=1, resource_type=ResourceType.IPC_CHANNEL,
                       resource_id=5, rights=Right.READ | Right.WRITE | Right.DELEGATE)
    child = mgr.delegate(parent.cap_id, to_pid=2, subset_rights=Right.READ)

    assert mgr.check(child.cap_id, ResourceType.IPC_CHANNEL, 5, Right.READ)
    assert not mgr.check(child.cap_id, ResourceType.IPC_CHANNEL, 5, Right.WRITE)
    assert child.owner_pid == 2


def test_delegate_cannot_expand_rights():
    mgr = CapabilityManager()
    parent = mgr.grant(owner_pid=1, resource_type=ResourceType.MEMORY,
                       resource_id=1, rights=Right.READ | Right.DELEGATE)
    with pytest.raises(CapabilityError):
        mgr.delegate(parent.cap_id, to_pid=2, subset_rights=Right.READ | Right.WRITE)


def test_delegate_requires_delegate_right():
    mgr = CapabilityManager()
    parent = mgr.grant(owner_pid=1, resource_type=ResourceType.MEMORY,
                       resource_id=1, rights=Right.READ)  # kein DELEGATE
    with pytest.raises(CapabilityError):
        mgr.delegate(parent.cap_id, to_pid=2, subset_rights=Right.READ)


def test_revoke_removes_capability():
    mgr = CapabilityManager()
    cap = mgr.grant(owner_pid=1, resource_type=ResourceType.MEMORY,
                    resource_id=1, rights=Right.READ)
    assert mgr.check(cap.cap_id, ResourceType.MEMORY, 1, Right.READ)
    n = mgr.revoke(cap.cap_id)
    assert n == 1
    assert not mgr.check(cap.cap_id, ResourceType.MEMORY, 1, Right.READ)


def test_revoke_cascades_to_delegated_children():
    mgr = CapabilityManager()
    parent = mgr.grant(owner_pid=1, resource_type=ResourceType.MEMORY,
                       resource_id=1, rights=Right.READ | Right.DELEGATE)
    child = mgr.delegate(parent.cap_id, to_pid=2, subset_rights=Right.READ)
    grandchild = mgr.delegate(child.cap_id, to_pid=3, subset_rights=Right.READ) \
        if child.has(Right.DELEGATE) else None

    n = mgr.revoke(parent.cap_id, cascade=True)
    assert not mgr.check(parent.cap_id, ResourceType.MEMORY, 1, Right.READ)
    assert not mgr.check(child.cap_id, ResourceType.MEMORY, 1, Right.READ)
    assert n >= 2


def test_capabilities_for_pid():
    mgr = CapabilityManager()
    mgr.grant(owner_pid=7, resource_type=ResourceType.MEMORY, resource_id=1, rights=Right.READ)
    mgr.grant(owner_pid=7, resource_type=ResourceType.IPC_CHANNEL, resource_id=2, rights=Right.WRITE)
    mgr.grant(owner_pid=8, resource_type=ResourceType.MEMORY, resource_id=3, rights=Right.READ)

    caps = mgr.capabilities_for_pid(7)
    assert len(caps) == 2
    assert all(c.owner_pid == 7 for c in caps)
