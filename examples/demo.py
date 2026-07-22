"""Runnable walk-through of the reference model.

    python examples/demo.py
"""
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from reversibility import ConsequenceTier, gate, gate_chain  # noqa: E402


def main() -> None:
    scenarios = yaml.safe_load(
        (pathlib.Path(__file__).resolve().parents[1] / "scenarios" / "scenarios.yaml").read_text()
    )
    print(f"{'scenario':<34}{'reversibility':<24}{'oversight':<20}{'evidence'}")
    print("-" * 96)
    for sc in scenarios:
        if "chain" in sc:
            cons = [ConsequenceTier[c] for c in sc["chain"]["consequences"]]
            g = gate_chain(sc["chain"]["declared_effects"], cons)
        else:
            g = gate(sc["declared_effect"], ConsequenceTier[sc["consequence"]])
        print(
            f"{sc['id']:<34}{g.reversibility.name.lower():<24}"
            f"{g.oversight.name.lower():<20}{g.evidence_tier}"
        )
    print()
    print("Note the two axes moving independently:")
    print("  low_consequence_but_irreversible  -> hard gate despite low blast radius")
    print("  high_consequence_but_reversible   -> elevated, but not treated as irreversible")


if __name__ == "__main__":
    main()
