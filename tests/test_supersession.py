"""Conformance coverage for the supersession event and finding channel.

observation.py states a normative requirement:

    Adapters MUST surface the flip (previous class, new class, as-of) as an
    event; flips toward a less restrictive class SHOULD additionally be
    reported as findings.

Before these tests the suite could not exercise either clause, so an
implementation could pass every scenario while emitting nothing. That is the
gap recorded in issue #6. These cases are deliberately kept out of the scenario
manifest: they assert a channel rather than a classification, and adding them
to scenarios/ would move the published N of M for a reason unrelated to corpus
coverage.
"""
from datetime import datetime, timedelta, timezone

import pytest

from reversibility import (
    ConsequenceTier,
    Observation,
    ObservationPolicy,
    ReversibilityClass,
    Binding,
    gate,
    supersession_direction,
)

NOW = datetime(2026, 8, 2, 12, 0, 0, tzinfo=timezone.utc)
THEN = NOW - timedelta(days=3)


def test_absent_supersession_is_unchanged_behaviour():
    """The default path must not move. Every existing result stays valid."""
    g = gate("read_only", ConsequenceTier.LOW)
    assert g.supersession is None
    assert g.finding is False
    assert g.oversight.name == "UNATTENDED"


@pytest.mark.parametrize(
    "previous,new,direction,finding",
    [
        ("non_recoverable", "recoverable_local", "permissive", True),
        ("externally_recoverable", "read_only", "permissive", True),
        ("recoverable_local", "externally_recoverable", "restrictive", False),
        ("read_only", "non_recoverable", "restrictive", False),
        ("non_recoverable", "externally_visible", "class_invariant", False),
    ],
)
def test_direction_and_finding(previous, new, direction, finding):
    """The SHOULD clause keys on direction, so direction has to be derived, not asserted."""
    g = gate(new, ConsequenceTier.HIGH, superseded=(previous, THEN))
    assert g.supersession.direction == direction
    assert g.finding is finding


def test_event_carries_previous_new_and_as_of():
    """The MUST names three fields. All three have to be addressable."""
    g = gate("recoverable_local", ConsequenceTier.LOW, superseded=("non_recoverable", THEN))
    assert g.supersession.previous is ReversibilityClass.IRREVERSIBLE
    assert g.supersession.new is ReversibilityClass.REVERSIBLE
    assert g.supersession.as_of == THEN


def test_event_survives_the_fail_closed_path():
    """The case issue #6 was filed about.

    A permissive flip whose new declaration has never been observed fails closed
    to IRREVERSIBLE. The state is correct either way, which is why a state-only
    fixture cannot tell a conforming implementation from a silent one. The event
    must still be surfaced, and the finding must still be raised.
    """
    g = gate(
        "recoverable_local",
        ConsequenceTier.HIGH,
        Observation(binding=Binding.UNOBSERVED, observed_as_of=THEN),
        ObservationPolicy(now=NOW),
        superseded=("non_recoverable", THEN),
    )
    assert g.reversibility is ReversibilityClass.IRREVERSIBLE  # fails closed
    assert g.supersession.direction == "permissive"            # and still says so
    assert g.finding is True


def test_naive_as_of_is_refused():
    """Consistent with Observation: the suite refuses naive datetimes at construction."""
    with pytest.raises(ValueError, match="timezone-aware"):
        gate("read_only", ConsequenceTier.LOW, superseded=("non_recoverable", datetime(2026, 8, 2)))


def test_direction_helper_is_the_existing_ordering():
    """Not new semantics: the same ladder required_oversight and chain_reversibility use."""
    R = ReversibilityClass
    assert supersession_direction(R.IRREVERSIBLE, R.READ_ONLY) == "permissive"
    assert supersession_direction(R.READ_ONLY, R.IRREVERSIBLE) == "restrictive"
    assert supersession_direction(R.REVERSIBLE, R.REVERSIBLE) == "class_invariant"
