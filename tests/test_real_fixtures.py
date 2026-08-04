"""Contributed corpus: real-data fixtures from a measured MCP registry corpus.

Separate from tests/test_conformance.py on purpose. The core suite publishes an
"N of M" denominator in RESULTS.md, so it must not learn that contributed corpora
exist - otherwise M moves whenever someone contributes and every prior published
row silently starts describing a different question.

Deleting scenarios/real.yaml and this file leaves the canonical suite untouched.
A second contributed corpus is a new pair of files, not an edit to a shared manifest.

Provenance, the annotation-to-class mapping, integrity digests, and the install
mapping for the generator's output block are in FIXTURES.md.
"""
import pytest

from conftest import assert_manifest, load_scenarios, run_scenario

SCENARIOS = load_scenarios("real.yaml")

# Same exact-set rule as the core manifest, scoped to this corpus: a contributed
# file that silently loses entries goes red rather than reporting a smaller pass.
EXPECTED_SCENARIO_IDS = frozenset(
    {
        "real_bound_readonly_tool",
        "real_stale_contract_mutation",
        "real_bound_aged_out",
        "real_unobserved_declared_tool",
        "real_flip_restrictive_state_only",
        "real_flip_permissive_state_only",
        "real_chain_stalest_link",
    }
)


def test_real_corpus_is_complete():
    assert_manifest(SCENARIOS, EXPECTED_SCENARIO_IDS)


def test_real_ids_are_prefixed():
    """The prefix is what keeps contributed ids from colliding with core ones."""
    unprefixed = sorted(s["id"] for s in SCENARIOS if not s["id"].startswith("real_"))
    assert not unprefixed, f"contributed ids must be prefixed: {unprefixed}"


def test_real_ids_do_not_collide_with_core():
    core = {s["id"] for s in load_scenarios("scenarios.yaml")}
    collisions = sorted({s["id"] for s in SCENARIOS} & core)
    assert not collisions, f"contributed ids collide with the core set: {collisions}"


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_real_scenarios(sc):
    run_scenario(sc)
