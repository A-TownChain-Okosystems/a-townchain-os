"""Tests fuer DID + Remote-Capability-Tickets. Nutzt ECHTE Ed25519-
Signaturen (kein Mock) -- Replay-Schutz, Signaturpruefung und
Delegationsketten sind reale, funktionierende Logik."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from shivaos.kernel.did import NodeIdentity
from shivaos.kernel.capabilities import Right, ResourceType
from shivaos.kernel.remote_capability import (
    ResourceDescriptor, Constraints, issue_ticket, RemoteCapabilityResolver,
    InvalidSignatureError, WrongSubjectError, ReplayError, ExpiredError,
    TicketError, LocalCap,
)


def make_resource():
    return ResourceDescriptor(ResourceType.MEMORY, resource_id=42, rights=Right.READ)


def make_constraints(ops=100, deadline_offset=60.0):
    return Constraints(max_operations=ops, deadline_unix=time.time() + deadline_offset)


def test_alice_bob_scenario_valid_ticket():
    """Bob delegiert Zugriff an Alice -- gueltiges Szenario aus der Spec."""
    bob = NodeIdentity.generate()
    alice = NodeIdentity.generate()
    ticket = issue_ticket(bob, alice.did, make_resource(), make_constraints())

    resolver = RemoteCapabilityResolver(own_did=alice.did)
    cap = resolver.resolve(ticket)
    assert isinstance(cap, LocalCap)
    assert cap.issuer_did == bob.did


def test_tampered_ticket_rejected():
    """Aendert jemand das Ticket nach der Signatur, muss die Pruefung fehlschlagen."""
    bob = NodeIdentity.generate()
    alice = NodeIdentity.generate()
    ticket = issue_ticket(bob, alice.did, make_resource(), make_constraints())

    tampered = ticket.__class__(
        issuer_did=ticket.issuer_did, subject_did=ticket.subject_did,
        resource=ResourceDescriptor(ResourceType.MEMORY, 999, Right.ALL),  # manipuliert!
        constraints=ticket.constraints, nonce=ticket.nonce,
        issuer_signature=ticket.issuer_signature,
    )
    resolver = RemoteCapabilityResolver(own_did=alice.did)
    with pytest.raises(InvalidSignatureError):
        resolver.resolve(tampered)


def test_wrong_subject_rejected():
    """Ticket ist fuer Alice bestimmt -- Charlie darf es nicht einloesen."""
    bob = NodeIdentity.generate()
    alice = NodeIdentity.generate()
    charlie = NodeIdentity.generate()
    ticket = issue_ticket(bob, alice.did, make_resource(), make_constraints())

    resolver = RemoteCapabilityResolver(own_did=charlie.did)
    with pytest.raises(WrongSubjectError):
        resolver.resolve(ticket)


def test_replay_attack_rejected():
    """Dasselbe Ticket zweimal einloesen -- der zweite Versuch muss scheitern."""
    bob = NodeIdentity.generate()
    alice = NodeIdentity.generate()
    ticket = issue_ticket(bob, alice.did, make_resource(), make_constraints())

    resolver = RemoteCapabilityResolver(own_did=alice.did)
    resolver.resolve(ticket)  # erster Versuch OK
    with pytest.raises(ReplayError):
        resolver.resolve(ticket)  # zweiter Versuch = Replay


def test_expired_ticket_rejected():
    bob = NodeIdentity.generate()
    alice = NodeIdentity.generate()
    ticket = issue_ticket(bob, alice.did, make_resource(),
                          make_constraints(deadline_offset=-10.0))  # schon abgelaufen
    resolver = RemoteCapabilityResolver(own_did=alice.did)
    with pytest.raises(ExpiredError):
        resolver.resolve(ticket)


def test_local_cap_enforces_max_operations():
    bob = NodeIdentity.generate()
    alice = NodeIdentity.generate()
    ticket = issue_ticket(bob, alice.did, make_resource(), make_constraints(ops=2))
    resolver = RemoteCapabilityResolver(own_did=alice.did)
    cap = resolver.resolve(ticket)

    cap.consume_operation()
    cap.consume_operation()
    with pytest.raises(TicketError):
        cap.consume_operation()  # drittes Mal -- max_operations=2 ueberschritten
    assert cap.revoked


def test_delegation_chain_bob_charlie_alice():
    """Bob -> Charlie -> Alice: mehrstufige Delegation mit Attenuation."""
    bob = NodeIdentity.generate()
    charlie = NodeIdentity.generate()
    alice = NodeIdentity.generate()

    ticket_to_charlie = issue_ticket(
        bob, charlie.did, ResourceDescriptor(ResourceType.MEMORY, 1, Right.READ | Right.WRITE),
        make_constraints(ops=100, deadline_offset=120.0))

    # Charlie schraenkt beim Weiterdelegieren an Alice ein (nur READ, weniger ops)
    ticket_to_alice = issue_ticket(
        charlie, alice.did, ResourceDescriptor(ResourceType.MEMORY, 1, Right.READ),
        make_constraints(ops=10, deadline_offset=60.0),
        parent_ticket_nonce=ticket_to_charlie.nonce)

    resolver = RemoteCapabilityResolver(own_did=alice.did)
    cap = resolver.resolve_chain([ticket_to_charlie, ticket_to_alice])
    assert cap.resource.rights == Right.READ
    assert cap.constraints.max_operations == 10


def test_delegation_chain_rejects_rights_expansion():
    """Charlie darf NICHT mehr Rechte weitergeben, als er selbst von Bob bekommen hat."""
    bob = NodeIdentity.generate()
    charlie = NodeIdentity.generate()
    alice = NodeIdentity.generate()

    ticket_to_charlie = issue_ticket(
        bob, charlie.did, ResourceDescriptor(ResourceType.MEMORY, 1, Right.READ),
        make_constraints())
    # Verstoss: Charlie versucht WRITE zu delegieren, obwohl er nur READ hatte
    ticket_to_alice = issue_ticket(
        charlie, alice.did, ResourceDescriptor(ResourceType.MEMORY, 1, Right.READ | Right.WRITE),
        make_constraints(), parent_ticket_nonce=ticket_to_charlie.nonce)

    resolver = RemoteCapabilityResolver(own_did=alice.did)
    with pytest.raises(TicketError):
        resolver.resolve_chain([ticket_to_charlie, ticket_to_alice])


def test_delegation_chain_rejects_broken_link():
    """parent_ticket_nonce zeigt auf nichts Passendes -- Kette ungueltig."""
    bob = NodeIdentity.generate()
    charlie = NodeIdentity.generate()
    alice = NodeIdentity.generate()

    ticket_to_charlie = issue_ticket(
        bob, charlie.did, make_resource(), make_constraints())
    ticket_to_alice = issue_ticket(
        charlie, alice.did, make_resource(), make_constraints(),
        parent_ticket_nonce="does-not-match")

    resolver = RemoteCapabilityResolver(own_did=alice.did)
    with pytest.raises(TicketError):
        resolver.resolve_chain([ticket_to_charlie, ticket_to_alice])
