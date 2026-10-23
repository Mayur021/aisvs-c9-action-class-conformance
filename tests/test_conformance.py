"""Conformance tests.

These encode the properties an implementation of reversibility-graded
action-class authority must satisfy. An implementation "conforms" if every test
here passes against it. The scenarios file is exercised end to end as well.
"""
import pathlib
import re
from datetime import datetime, timedelta

import pytest

from reversibility import (
    Binding,
    ConsequenceTier,
    Observation,
    ObservationPolicy,
    Oversight,
    ReversibilityClass,
    chain_binding,
    chain_reversibility,
    chain_within_approved,
    classify,
    coverage,
    declaration_is_usable,
    effective_binding,
    gate,
    gate_chain,
    gate_chain_extension,
    recognised_effect,
    required_oversight,
)

from conftest import (  # noqa: E402  - shared with contributed-corpus suites
    NOW,
    assert_manifest,
    load_scenarios,
    run_scenario,
)


# The core set only. This module must stay unaware that contributed corpora exist:
# RESULTS.md publishes "N of M" against this manifest, so a canonical denominator
# that grew whenever someone contributed would silently redefine every prior row.
SCENARIOS = load_scenarios("scenarios.yaml")


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

# The scenario corpus is pinned by name. Parametrising over whatever the file
# happens to contain means a corpus that loses entries still reports green, and
# a run against a shrunken corpus produces a smaller "N of M matched" that reads
# as an honest partial result rather than a broken suite. Adding or removing a
# scenario has to be a deliberate edit here as well as in the YAML.
EXPECTED_SCENARIO_IDS = frozenset(
    {
        "read_only_report",
        "local_config_edit",
        "merge_to_shared_branch",
        "production_external_release",
        "unclassified_action_fails_closed",
        "low_consequence_but_irreversible",
        "high_consequence_but_reversible",
        "composed_chain_worst_case",
        "bound_declaration_is_honoured",
        "stale_declaration_fails_closed",
        "unobserved_is_not_agreement",
        "bound_but_expired_ages_out",
        "chain_is_as_stale_as_its_stalest_link",
    }
)


def test_scenario_corpus_is_complete():
    """The corpus cannot shrink or grow without this test being updated.

    The id comparison is set-based, so two scenarios sharing an id would
    collapse to one entry and pass while the parametrised run executed an
    extra case. Duplicates are rejected first, against the list.
    """
    assert_manifest(SCENARIOS, EXPECTED_SCENARIO_IDS)


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_worked_scenarios(sc):
    run_scenario(sc)


# --- Property 8: declaration-only remains the default and is unchanged --------

def test_no_observation_means_declaration_only_mode():
    g = gate("read_only", ConsequenceTier.LOW)
    assert g.mode == "declaration-only"
    assert g.binding is None


def test_declaration_only_results_are_unchanged_by_the_new_input():
    # Every pre-observation verdict must survive. This is the backward
    # compatibility guarantee an earlier conformance run depends on.
    for eff in ["read_only", "recoverable_local", "externally_recoverable",
                "non_recoverable", "externally_visible", None, "not_a_real_effect"]:
        for c in ConsequenceTier:
            g = gate(eff, c)
            assert g.oversight is required_oversight(classify(eff), c)
            assert g.mode == "declaration-only"


def test_chain_declaration_only_unchanged():
    g = gate_chain(["read_only", "read_only", "non_recoverable"])
    assert g.mode == "declaration-only"
    assert g.binding is None
    assert g.reversibility is ReversibilityClass.IRREVERSIBLE


# --- Property 9: three states for the record, two outcomes for the gate -------

def test_three_binding_states_exist_and_are_ordered():
    assert [b.name for b in Binding] == ["BOUND", "STALE", "UNOBSERVED"]
    assert Binding.BOUND < Binding.STALE < Binding.UNOBSERVED


def test_only_bound_is_usable():
    assert declaration_is_usable(Binding.BOUND)
    assert not declaration_is_usable(Binding.STALE)
    assert not declaration_is_usable(Binding.UNOBSERVED)


def test_stale_and_unobserved_are_distinct_in_the_record_same_at_the_gate():
    stale = gate("read_only", ConsequenceTier.LOW,
                 Observation(Binding.STALE), ObservationPolicy(now=NOW))
    unobs = gate("read_only", ConsequenceTier.LOW,
                 Observation(Binding.UNOBSERVED), ObservationPolicy(now=NOW))
    # same gate outcome
    assert stale.oversight is unobs.oversight is Oversight.HUMAN_OWNS
    # distinct in the record, which is what makes the binding gap computable
    assert stale.binding is not unobs.binding


# --- Property 10: absence is not agreement ------------------------------------

def test_absent_observation_inside_observation_mode_is_unobserved():
    # Passing no observation is declaration-only. Passing an explicit
    # unobserved is the layer having looked and failed to attest.
    assert effective_binding(None) is Binding.UNOBSERVED


def test_bound_declaration_is_honoured():
    g = gate("read_only", ConsequenceTier.LOW,
             Observation(Binding.BOUND, NOW - timedelta(days=1)),
             ObservationPolicy(now=NOW))
    assert g.reversibility is ReversibilityClass.READ_ONLY
    assert g.oversight is Oversight.UNATTENDED
    assert g.mode == "declaration+observation"


# --- Property 11: observations expire, on a clock -----------------------------

def test_bound_observation_ages_out_to_unobserved_not_stale():
    old = Observation(Binding.BOUND, NOW - timedelta(days=400))
    pol = ObservationPolicy(max_age=timedelta(days=30), now=NOW)
    assert effective_binding(old, pol) is Binding.UNOBSERVED


def test_fresh_bound_observation_survives_the_clock():
    fresh = Observation(Binding.BOUND, NOW - timedelta(days=1))
    pol = ObservationPolicy(max_age=timedelta(days=30), now=NOW)
    assert effective_binding(fresh, pol) is Binding.BOUND


def test_no_max_age_means_no_expiry():
    old = Observation(Binding.BOUND, NOW - timedelta(days=4000))
    assert effective_binding(old, ObservationPolicy(now=NOW)) is Binding.BOUND


def test_future_dated_observation_does_not_outrun_the_clock():
    # A negative age is under every maximum, so without this the entry would
    # never age out at any policy - the permanent-verification failure the
    # constructor's as-of rule exists to prevent, reached from the other side.
    ahead = Observation(Binding.BOUND, NOW + timedelta(days=1))
    pol = ObservationPolicy(max_age=timedelta(days=30), now=NOW)
    assert effective_binding(ahead, pol) is Binding.UNOBSERVED
    assert gate("read_only", ConsequenceTier.LOW, ahead, pol).oversight is Oversight.HUMAN_OWNS


def test_future_dated_fails_closed_even_with_no_expiry_policy():
    # max_age=None means observations do not age out. It does not mean an as-of
    # the clock has not reached yet is usable.
    ahead = Observation(Binding.BOUND, NOW + timedelta(days=1))
    assert effective_binding(ahead, ObservationPolicy(now=NOW)) is Binding.UNOBSERVED


def test_naive_timestamps_are_rejected_at_the_boundary_not_on_the_path():
    # datetime.utcnow() returns a naive datetime, so this is the default mistake
    # rather than an exotic one. Comparing it against the policy clock raises
    # TypeError, and a raise on the decision path is an open gate to any caller
    # that reads an exception as no-policy-applied. It is refused at authoring
    # time, where nothing can mistake it for a verdict.
    naive = datetime(2026, 8, 1, 12, 0, 0)
    with pytest.raises(ValueError):
        Observation(Binding.BOUND, naive)
    with pytest.raises(ValueError):
        ObservationPolicy(now=naive)


def test_bound_observation_requires_an_as_of():
    # A bound state with no age cannot expire and would read as permanently
    # verified, which is the failure this whole input exists to prevent.
    with pytest.raises(ValueError):
        Observation(Binding.BOUND)


# --- Property 12: a chain is as stale as its stalest link ---------------------

def test_chain_binding_takes_the_worst_link():
    assert chain_binding([Binding.BOUND, Binding.BOUND]) is Binding.BOUND
    assert chain_binding([Binding.BOUND, Binding.STALE]) is Binding.STALE
    assert chain_binding([Binding.BOUND, Binding.UNOBSERVED]) is Binding.UNOBSERVED
    assert chain_binding([Binding.STALE, Binding.UNOBSERVED]) is Binding.UNOBSERVED


def test_empty_chain_binding_fails_closed():
    assert chain_binding([]) is Binding.UNOBSERVED


def test_one_unbound_link_hard_gates_an_otherwise_read_only_chain():
    g = gate_chain(
        ["read_only", "read_only", "read_only"],
        [ConsequenceTier.LOW] * 3,
        [Observation(Binding.BOUND, NOW - timedelta(days=1)),
         Observation(Binding.STALE),
         Observation(Binding.BOUND, NOW - timedelta(days=1))],
        ObservationPolicy(now=NOW),
    )
    assert g.binding is Binding.STALE
    assert g.reversibility is ReversibilityClass.IRREVERSIBLE
    assert g.oversight is Oversight.HUMAN_OWNS


# --- Property 13: the binding gap is computable and only in observation mode --

def test_binding_gap_is_declared_minus_verified():
    bound = Observation(Binding.BOUND, NOW - timedelta(days=1))
    pol = ObservationPolicy(now=NOW)
    actions = [
        ("read_only", bound),                      # declared, verified
        ("recoverable_local", bound),              # declared, verified
        ("read_only", Observation(Binding.STALE)),  # declared, not verified
        ("read_only", Observation(Binding.UNOBSERVED)),  # declared, not verified
        (None, bound),                             # not declared at all
    ]
    cov = coverage(actions, recognised_effect, pol)
    assert cov.population == 5
    assert cov.declared == pytest.approx(4 / 5)
    assert cov.verified == pytest.approx(2 / 5)
    assert cov.binding_gap == pytest.approx(2 / 5)


def test_unrecognised_effect_counts_against_declared_coverage():
    bound = Observation(Binding.BOUND, NOW - timedelta(days=1))
    cov = coverage([("not_a_real_effect", bound)], recognised_effect,
                   ObservationPolicy(now=NOW))
    assert cov.declared == 0.0
    assert cov.verified == 0.0


# --- Property 14: the package names one release, not two ----------------------

def test_package_version_matches_the_distribution_version():
    """RESULTS.md pins every row to a suite release, and the obvious way to fill
    that cell is to read reversibility.__version__. Where it disagrees with the
    version the package was built as, a row names a release nobody ran, under a
    digest that makes it look settled.

    pyproject is read with a regex rather than tomllib, which arrives in 3.11
    while this package supports 3.9.
    """
    import reversibility

    pyproject = (pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()
    declared = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
    assert declared, "pyproject.toml has no version line"
    assert reversibility.__version__ == declared.group(1)


# --- Property 15: who established the chain's extent (C9.2.10, 1.01) ----------

def test_provenance_silence_leaves_the_verdict_unchanged():
    """Adding the input must not move a result that predates it."""
    effects = ["read_only", "recoverable_local"]
    before = gate_chain(effects, [ConsequenceTier.LOW, ConsequenceTier.LOW])
    after = gate_chain(
        effects, [ConsequenceTier.LOW, ConsequenceTier.LOW],
        chain_established_externally=None,
    )
    assert before.reversibility is after.reversibility
    assert before.oversight is after.oversight
    assert before.rationale == after.rationale
    assert after.finding is False


def test_externally_established_chain_is_recorded_not_penalised():
    g = gate_chain(
        ["read_only", "recoverable_local"],
        [ConsequenceTier.LOW, ConsequenceTier.LOW],
        chain_established_externally=True,
    )
    assert g.reversibility is ReversibilityClass.REVERSIBLE
    assert g.finding is False
    assert "established outside the gated agent" in g.rationale


def test_agent_supplied_chain_extent_fails_closed_and_is_a_finding():
    """A fold over a set the gated party chose is not a bound on that party."""
    g = gate_chain(
        ["read_only", "read_only"],
        [ConsequenceTier.LOW, ConsequenceTier.LOW],
        chain_established_externally=False,
    )
    assert g.reversibility is ReversibilityClass.IRREVERSIBLE
    assert g.oversight is Oversight.HUMAN_OWNS
    assert g.finding is True
    assert "supplied by the gated agent" in g.rationale


# --- Property 16: execution beyond the approved chain (C9.2.11, 1.01) --------

def test_attempt_within_the_approved_chain_is_covered():
    assert chain_within_approved(["read_only", "recoverable_local"], ["read_only"])
    assert chain_within_approved(["read_only"], ["read_only"])
    assert chain_within_approved(["read_only"], [])


def test_longer_reordered_or_substituted_attempts_exceed_the_approval():
    assert not chain_within_approved(["read_only"], ["read_only", "read_only"])
    assert not chain_within_approved(
        ["read_only", "recoverable_local"], ["recoverable_local", "read_only"]
    )
    assert not chain_within_approved(["read_only"], ["non_recoverable"])


def test_attempt_inside_the_approval_keeps_the_existing_gate():
    g = gate_chain_extension(
        ["read_only", "recoverable_local"],
        ["read_only"],
        [ConsequenceTier.LOW, ConsequenceTier.LOW],
    )
    assert g.finding is False
    assert g.oversight is Oversight.SUPERVISED
    assert "existing approval stands" in g.rationale


def test_exceeding_the_approval_is_blocked_pending_new_approval():
    """Floor is APPROVAL_REQUIRED even where the cumulative class sits below it."""
    g = gate_chain_extension(
        ["read_only"],
        ["read_only", "read_only"],
        [ConsequenceTier.LOW, ConsequenceTier.LOW],
    )
    assert g.finding is True
    assert g.reversibility is ReversibilityClass.READ_ONLY
    assert g.oversight is Oversight.APPROVAL_REQUIRED
    assert "blocked pending new approval" in g.rationale


def test_re_approval_is_gated_on_the_cumulative_chain_not_the_extension():
    """The extension alone is read-only; the cumulative chain is not."""
    g = gate_chain_extension(
        ["externally_recoverable"],
        ["externally_recoverable", "read_only"],
        [ConsequenceTier.LOW, ConsequenceTier.LOW],
    )
    assert g.reversibility is ReversibilityClass.EXTERNALLY_REVERSIBLE
    assert g.oversight is Oversight.APPROVAL_REQUIRED
    assert "cumulative chain of 2 step(s)" in g.rationale


def test_an_irreversible_step_beyond_the_approval_reaches_the_hard_gate():
    g = gate_chain_extension(
        ["read_only"],
        ["read_only", "non_recoverable"],
        [ConsequenceTier.LOW, ConsequenceTier.LOW],
    )
    assert g.reversibility is ReversibilityClass.IRREVERSIBLE
    assert g.oversight is Oversight.HUMAN_OWNS
    assert g.finding is True
