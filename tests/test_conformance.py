"""Conformance tests.

These encode the properties an implementation of reversibility-graded
action-class authority must satisfy. An implementation "conforms" if every test
here passes against it. The scenarios file is exercised end to end as well.
"""
import pathlib

import pytest
import yaml

from reversibility import (
    ConsequenceTier,
    Oversight,
    ReversibilityClass,
    classify,
    gate,
    gate_chain,
    required_oversight,
    chain_reversibility,
)

SCENARIOS = yaml.safe_load(
    (pathlib.Path(__file__).resolve().parents[1] / "scenarios" / "scenarios.yaml").read_text()
)


# --- Property 1: the four classes exist and are ordered -----------------------

def test_four_classes_present_and_ordered():
    names = [c.name for c in ReversibilityClass]
    assert names == ["READ_ONLY", "REVERSIBLE", "EXTERNALLY_REVERSIBLE", "IRREVERSIBLE"]
    assert (
        ReversibilityClass.READ_ONLY
        < ReversibilityClass.REVERSIBLE
        < ReversibilityClass.EXTERNALLY_REVERSIBLE
        < ReversibilityClass.IRREVERSIBLE
    )


def test_externally_reversible_is_distinct_from_reversible():
    # The rung most implementations lose must be its own class with its own gate.
    assert (
        required_oversight(ReversibilityClass.EXTERNALLY_REVERSIBLE)
        != required_oversight(ReversibilityClass.REVERSIBLE)
    )


# --- Property 2: fail-closed on unknown / undeclared --------------------------

def test_unclassified_fails_closed_to_irreversible():
    assert classify(None) is ReversibilityClass.IRREVERSIBLE
    assert classify("something_not_in_the_registry") is ReversibilityClass.IRREVERSIBLE
    assert gate(None).oversight is Oversight.HUMAN_OWNS


def test_empty_chain_fails_closed():
    assert chain_reversibility([]) is ReversibilityClass.IRREVERSIBLE


# --- Property 3: class is derived from declared effect, not asserted ----------

def test_class_comes_from_declared_effect():
    assert classify("read_only") is ReversibilityClass.READ_ONLY
    assert classify("externally_recoverable") is ReversibilityClass.EXTERNALLY_REVERSIBLE
    assert classify("non_recoverable") is ReversibilityClass.IRREVERSIBLE


# --- Property 4: oversight monotonic in reversibility -------------------------

def test_oversight_monotonic_in_reversibility():
    ovs = [required_oversight(r) for r in ReversibilityClass]
    assert ovs == sorted(ovs)
    assert ovs[0] == Oversight.UNATTENDED
    assert ovs[-1] == Oversight.HUMAN_OWNS


# --- Property 5: reversibility and consequence are independent axes -----------

def test_low_consequence_irreversible_still_hard_gate():
    g = gate("non_recoverable", ConsequenceTier.LOW)
    assert g.reversibility is ReversibilityClass.IRREVERSIBLE
    assert g.oversight is Oversight.HUMAN_OWNS  # low consequence does not soften it


def test_high_consequence_reversible_is_elevated_not_hard_stopped():
    g = gate("recoverable_local", ConsequenceTier.HIGH)
    assert g.reversibility is ReversibilityClass.REVERSIBLE
    # elevated by consequence, but not treated as irreversible
    assert Oversight.SUPERVISED < g.oversight < Oversight.HUMAN_OWNS


def test_oversight_is_worse_of_both_axes():
    # worse axis wins in both directions
    assert gate("read_only", ConsequenceTier.CRITICAL).oversight is Oversight.HUMAN_OWNS
    assert gate("non_recoverable", ConsequenceTier.LOW).oversight is Oversight.HUMAN_OWNS


# --- Property 6: worst-case across a composed chain ---------------------------

def test_chain_gated_at_worst_case_from_commencement():
    g = gate_chain(
        ["read_only", "recoverable_local", "externally_recoverable"],
        [ConsequenceTier.LOW, ConsequenceTier.LOW, ConsequenceTier.HIGH],
    )
    assert g.reversibility is ReversibilityClass.EXTERNALLY_REVERSIBLE
    assert g.oversight is Oversight.APPROVAL_REQUIRED


def test_chain_with_hidden_irreversible_step_is_hard_gated():
    g = gate_chain(["read_only", "read_only", "non_recoverable"])
    assert g.reversibility is ReversibilityClass.IRREVERSIBLE
    assert g.oversight is Oversight.HUMAN_OWNS


# --- Property 7: every worked scenario resolves as documented -----------------

@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_worked_scenarios(sc):
    exp = sc["expect"]
    if "chain" in sc:
        cons = [ConsequenceTier[c] for c in sc["chain"]["consequences"]]
        g = gate_chain(sc["chain"]["declared_effects"], cons)
    else:
        g = gate(sc["declared_effect"], ConsequenceTier[sc["consequence"]])
    assert g.reversibility.name == exp["reversibility"]
    assert g.oversight.name == exp["oversight"]
    assert g.evidence_tier == exp["evidence_tier"]
