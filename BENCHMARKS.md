# Benchmarks

What the reference implementation does when pointed at observed data, measured
per release. Correctness is in `RESULTS.md` and the test suite. This file is
about cost, and about what the gate decides on a real population.

## Corpus

`declared_vectors_v1.csv` from the deposit at DOI 10.5281/zenodo.21778282,
37,001 rows, one per server and tool pair. `bench/fetch.py`
downloads it and checks it against the digest the deposit publishes, so a run is
pinned to the depositor's bytes rather than to a copy kept here.

The deposit's own scope limit applies to everything below and is quoted rather
than paraphrased: it "records that published contracts (description, inputSchema,
outputSchema) mutated after a declared-effect annotation was observed,
declaration staleness, not declaration falsity. No runtime behaviour is observed;
no action is ever witnessed executing." So these numbers describe what a gate
decides when handed declared inputs. They say nothing about whether a tool's
declaration is true, and nothing here should be read as evidence that it is.

The deposit imputes nothing: absent means undeclared rather than false. That is
the right choice for a measurement. A gate cannot make it, because it has to
resolve absence before it can decide. Both resolutions are reported below, and
neither is presented as a correction to the deposit. The distinction between a
measurement that may not impute and a gate that must is Ishaan Ghosh's.

## What resolving absence costs

MCP spec defaults, at revision 2026-07-28: `readOnlyHint` false,
`destructiveHint` true, `idempotentHint` false, `openWorldHint` true.

| Class | absent is undeclared | spec defaults imputed | delta |
|---|---|---|---|
| `READ_ONLY` | 30799 | 30799 | +0 |
| `REVERSIBLE` | 2382 | 2546 | +164 |
| `EXTERNALLY_REVERSIBLE` | 1830 | 2030 | +200 |
| `IRREVERSIBLE` | 1990 | 1626 | -364 |

364 tools leave the irreversible class, 18.3% of it, purely by choosing to
impute the spec default rather than fail closed on absence. Those tools drop out
of `HUMAN_OWNS` oversight. The choice is usually made silently. This is what it
costs.

706 tools are undeclared under the strict reading, and all of them fail closed
to `IRREVERSIBLE`.

## Latency

Microseconds, over the full corpus.

| Primitive | p50 | p95 | p99 |
|---|---|---|---|
| `classify` | 0.1 | 0.2 | 0.3 |
| `required_oversight` | 1.3 | 2.4 | 2.6 |
| `gate` | 4.2 | 8.2 | 8.8 |

## Chain scaling

Microseconds per action, so a falling column means fixed overhead amortising
over a linear fold.

| Chain length | `chain_reversibility` | `gate_chain` |
|---|---|---|
| 1 | 0.6 | 5.5 |
| 10 | 0.07 | 0.69 |
| 100 | 0.026 | 0.185 |
| 1000 | 0.0199 | 0.1264 |

## Limits

The deposit carries no consequence information, so every action is gated at
`ConsequenceTier.LOW`. This measures the reversibility axis only. Because
`required_oversight` takes the worse of the two axes, real oversight can only be
higher than reported here, never lower.

Timings come from a developer machine rather than an isolated host and are
indicative. They are not comparable to figures another project reports from a
dedicated environment. Run `python bench/bench.py` to produce your own.

| Run | Suite | Date | Environment |
|---|---|---|---|
| 1 | 1.2.0 | 2026-10-05 | python 3.13.12, WSL2 x86_64 |
