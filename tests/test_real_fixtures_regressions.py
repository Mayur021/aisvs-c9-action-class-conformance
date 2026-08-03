"""Regression guards for the two fail-open behaviors flagged on the observation PR.

Both are xfail(strict=True) against v1.1.1: the release notes state the fail-open
fix ships as its own tag. strict=True makes the XPASS at that tag fail CI, forcing
marker removal in the same commit as the fix - converting both tests into permanent
fail-closed guards. See FIXTURES.md for the operational reading.
"""
import pytest

from reversibility.chain import gate_chain
from reversibility.model import (
    ConsequenceTier,
    Oversight,
    ReversibilityClass,
    classify,
)

XFAIL_REASON = "fail-open fix ships as its own tag per v1.1.1 release notes"

STEPS = ["read_only", "externally_recoverable"]


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_short_consequence_list_fails_closed():
    """A consequence list shorter than its steps must resolve every unaccounted
    step to the most restrictive tier, and the rationale must record that a step
    went unaccounted - a gate that silently strengthens is nearly as illegible
    as one that silently weakens."""
    result = gate_chain(STEPS, [ConsequenceTier.LOW])
    assert result.oversight is Oversight.HUMAN_OWNS
    assert result.consequence is ConsequenceTier.CRITICAL
    assert "unaccounted" in result.rationale


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_empty_consequence_list_fails_closed():
    """An empty consequence list is every step unaccounted - not a default to
    the weakest tier."""
    result = gate_chain(STEPS, [])
    assert result.oversight is Oversight.HUMAN_OWNS
    assert result.consequence is ConsequenceTier.CRITICAL


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_none_consequences_declined_axis_fails_closed():
    """consequences=None declines the axis entirely: same strongest-tier verdict
    as unaccounted steps, distinct recorded basis. Kept as its own test so a
    divergent owner intent for the None shape reddens one function, not three."""
    result = gate_chain(STEPS, None)
    assert result.oversight is Oversight.HUMAN_OWNS
    assert result.consequence is ConsequenceTier.CRITICAL


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_unhashable_effect_fails_closed_not_raise():
    """An unhashable declared effect is unrecognised input on the decision path:
    the docstring already promises unrecognised fails closed to irreversible,
    and a list is certainly unrecognised. It must classify, never raise - a
    caller reading an exception as no-policy-applied turns a raise into an
    open gate."""
    result = classify(["read_only"])
    assert result is ReversibilityClass.IRREVERSIBLE
