"""Benchmark the reference implementation against observed MCP declarations.

Corpus: declared_vectors_v1.csv from Gautam Bharti's deposit,
DOI 10.5281/zenodo.21778282, 37,001 rows, one per (server_id, tool_id).

Limitation stated up front: the deposit carries no consequence information, so
every action here is gated at ConsequenceTier.LOW. This measures the
reversibility axis only. A deployment supplies consequence from its own policy,
and required_oversight takes the worse of the two axes, so real oversight can
only be higher than what is reported here, never lower.
"""
import csv, json, platform, statistics, sys, time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reversibility import (
    ConsequenceTier, ReversibilityClass, chain_reversibility, classify,
    gate, gate_chain, required_oversight, __version__,
)
from bench.corpus import declared_effect

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "declared_vectors_v1.csv"


def percentiles(samples):
    s = sorted(samples)
    n = len(s)
    def p(q):
        return s[min(n - 1, int(q * n))]
    return {"p50": round(p(0.50), 3), "p95": round(p(0.95), 3),
            "p99": round(p(0.99), 3), "n": n}


def time_us(fn, arg, reps=5):
    """Microseconds per call, best of reps timed batches."""
    best = None
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        fn(arg)
        dt = (time.perf_counter_ns() - t0) / 1000.0
        best = dt if best is None else min(best, dt)
    return best


def run():
    rows = list(csv.DictReader(DATA.open()))
    out = {
        "suite_version": __version__,
        "corpus": {
            "source": "declared_vectors_v1.csv",
            "doi": "10.5281/zenodo.21778282",
            "rows": len(rows),
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "timing_caveat": "indicative, not an isolated host",
        },
        "modes": {},
        "latency_us": {},
        "chain_scaling_us_per_action": {},
    }

    for mode, resolve in (("strict_absent_is_undeclared", False),
                          ("spec_defaults_imputed", True)):
        effects = [declared_effect(r, resolve) for r in rows]
        classes = [classify(e) for e in effects]
        oversight = [required_oversight(c, ConsequenceTier.LOW) for c in classes]
        undeclared = sum(1 for e in effects if e is None)
        out["modes"][mode] = {
            "class": {k.name: v for k, v in sorted(Counter(classes).items())},
            "oversight": {k.name: v for k, v in sorted(Counter(oversight).items())},
            "undeclared": undeclared,
            "undeclared_all_irreversible": all(
                classify(e) is ReversibilityClass.IRREVERSIBLE
                for e in effects if e is None
            ),
        }

    sample = [declared_effect(r, True) for r in rows]
    out["latency_us"]["classify"] = percentiles(
        [time_us(classify, e) for e in sample])
    out["latency_us"]["required_oversight"] = percentiles(
        [time_us(lambda c: required_oversight(c, ConsequenceTier.LOW),
                 classify(e)) for e in sample])
    out["latency_us"]["gate"] = percentiles(
        [time_us(lambda e: gate(e, ConsequenceTier.LOW), e) for e in sample])

    pool = [e for e in sample if e is not None]
    for n in (1, 10, 100, 1000):
        chain = [pool[i % len(pool)] for i in range(n)]
        cls = [classify(e) for e in chain]
        t_fold = min(time_us(chain_reversibility, cls) for _ in range(5))
        t_gate = min(time_us(gate_chain, chain) for _ in range(5))
        out["chain_scaling_us_per_action"][str(n)] = {
            "chain_reversibility": round(t_fold / n, 4),
            "gate_chain": round(t_gate / n, 4),
        }
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps(r, indent=2))
