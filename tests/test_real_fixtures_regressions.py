"""Permanent fail-closed guards for the behaviors flagged on the observation PR.

These were xfail(strict=True) against v1.1.1, pending the fail-open fix tag named
in that release's notes. The fix is v1.2.0 and the markers came off in the same
commit, which is what strict=True existed to force: the fix made all four XPASS
and reddened CI. They are ordinary tests now, so a regression on any of these
paths fails the build instead of being absorbed as an expected failure. See
FIXTURES.md for the operational reading.
"""
from reversibility.chain import gate_chain
from reversibility.model import (
    ConsequenceTier,
    Oversight,
    ReversibilityClass,
    classify,
)

STEPS = ["read_only", "externally_recoverable"]


def test_short_consequence_list_fails_closed():
    """A consequence list shorter than its steps must resolve every unaccounted
    step to the most restrictive tier, and the rationale must record that a step
    went unaccounted - a gate that silently strengthens is nearly as illegible
    as one that silently weakens."""
    result = gate_chain(STEPS, [ConsequenceTier.LOW])
    assert result.oversight is Oversight.HUMAN_OWNS
    assert result.consequence is ConsequenceTier.CRITICAL
    assert "unaccounted" in result.rationale


def test_empty_consequence_list_fails_closed():
    """An empty consequence list is every step unaccounted - not a default to
    the weakest tier."""
    result = gate_chain(STEPS, [])
    assert result.oversight is Oversight.HUMAN_OWNS
    assert result.consequence is ConsequenceTier.CRITICAL


def test_none_consequences_declined_axis_fails_closed():
    """consequences=None declines the axis entirely: same strongest-tier verdict
    as unaccounted steps, distinct recorded basis. Kept as its own test so a
    divergent owner intent for the None shape reddens one function, not three."""
    result = gate_chain(STEPS, None)
    assert result.oversight is Oversight.HUMAN_OWNS
    assert result.consequence is ConsequenceTier.CRITICAL


def test_unhashable_effect_fails_closed_not_raise():
    """An unhashable declared effect is unrecognised input on the decision path:
    the docstring already promises unrecognised fails closed to irreversible,
    and a list is certainly unrecognised. It must classify, never raise - a
    caller reading an exception as no-policy-applied turns a raise into an
    open gate."""
    result = classify(["read_only"])
    assert result is ReversibilityClass.IRREVERSIBLE
