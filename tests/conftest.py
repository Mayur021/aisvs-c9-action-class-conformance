"""Shared scenario helpers.

The core conformance suite and any contributed corpus exercise scenarios the same
way; only the file they load and the manifest they assert against differ. Keeping
the helpers here is what lets tests/test_conformance.py stay unaware that
contributed corpora exist at all.
"""
import pathlib
from datetime import datetime, timedelta, timezone

import yaml

from reversibility import (
    Binding,
    ConsequenceTier,
    Observation,
    ObservationPolicy,
    gate,
    gate_chain,
)

SCENARIO_DIR = pathlib.Path(__file__).resolve().parents[1] / "scenarios"

# Fixed so a conformance run is reproducible rather than dependent on when it ran.
NOW = datetime(2026, 8, 2, 12, 0, 0, tzinfo=timezone.utc)


def load_scenarios(name):
    """Load one scenario file from scenarios/ by filename."""
    return yaml.safe_load((SCENARIO_DIR / name).read_text())


def obs(spec):
    """Build an Observation from a scenario's observation block."""
    if spec is None:
        return None
    b = Binding[spec["binding"]]
    as_of = NOW - timedelta(days=spec["age_days"]) if "age_days" in spec else None
    return Observation(binding=b, observed_as_of=as_of)


def policy(spec):
    if spec is None:
        return ObservationPolicy(now=NOW)
    return ObservationPolicy(
        max_age=timedelta(days=spec["max_age_days"]) if "max_age_days" in spec else None,
        now=NOW,
    )


def run_scenario(sc):
    """Evaluate one scenario and assert it matches its declared expectations."""
    exp = sc["expect"]
    pol = policy(sc.get("policy"))
    if "chain" in sc:
        ch = sc["chain"]
        cons = [ConsequenceTier[c] for c in ch["consequences"]]
        observations = (
            [obs(o) for o in ch["observations"]] if "observations" in ch else None
        )
        g = gate_chain(
            ch["declared_effects"], cons, observations, pol if observations else None
        )
    else:
        o = obs(sc.get("observation"))
        g = gate(
            sc["declared_effect"],
            ConsequenceTier[sc["consequence"]],
            o,
            pol if o else None,
        )
    assert g.reversibility.name == exp["reversibility"]
    assert g.oversight.name == exp["oversight"]
    assert g.evidence_tier == exp["evidence_tier"]


def assert_manifest(scenarios, expected_ids):
    """Exact-set check against a declared manifest.

    Exact rather than subset on purpose: a corpus that silently loses entries has
    to go red rather than report a smaller, honest-looking pass. Adding or removing
    a scenario is a deliberate edit in two places.
    """
    ids = [s["id"] for s in scenarios]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    assert not duplicates, f"duplicate scenario ids: {duplicates}"
    found = set(ids)
    assert found == expected_ids, (
        f"missing: {sorted(expected_ids - found)}, "
        f"unexpected: {sorted(found - expected_ids)}"
    )
