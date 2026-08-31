# Reversibility-graded action-class authority: reference implementation

**Live demo:** https://mayur021.github.io/aisvs-c9-action-class-conformance/

A small, dependency-light reference model and conformance suite for grading how
much oversight an agent's action needs by how hard that action is to undo. It
implements the classification and gating primitives behind OWASP AISVS v1.0
chapter C9 (Orchestration & Agentic Security), so an implementation can
be checked against a single, explicit definition rather than each one inventing
its own.

The point it makes concrete: a completed check is evidence of what was looked
at, not authority to act. Whether an action may run unattended, or must be owned
by a named human, follows from the class of the action, evaluated outside the
model that proposed it.

## The model in five ideas

**1. Four classes, including the two usually lost.**

| Class | Meaning |
|---|---|
| `read_only` | Observes state, changes nothing. |
| `reversible` | Recoverable local state you can restore yourself. |
| `externally_reversible` | Recoverable only by a party other than you (a published artefact, a sent message, a payment the counterparty must reverse). |
| `irreversible` | Cannot be walked back once it runs. |

`externally_reversible` is a distinct rung, not a shade of `reversible`, because
you cannot unilaterally undo it. `irreversible` is a hard class, not the top of a
"difficult to reverse" spectrum, because its gate is a stop by definition.

**2. Reversibility and consequence are independent axes.**

Blast radius and undo-ability correlate but are not the same signal. A
low-consequence action can be irreversible (a small deletion with no backup); a
high-consequence action can be fully reversible (a large but restorable config
change). Required oversight is a function of **both**, taking the worse of the
two. Collapsing them into one scale throws away the signal reversibility exists
to carry.

**3. Fail closed.**

An action whose class is undeclared or unrecognised is treated as the most
restrictive class. Omitting the classification cannot quietly lower the bar.

The same rule runs wherever an input is missing rather than wrong. A chain step
carrying no consequence is unaccounted rather than low, and every unaccounted
step resolves to the strongest tier. An observation dated ahead of the clock is
unusable rather than very fresh, because a negative age is under every maximum
and would never expire at any policy. And malformed input on the decision path
returns a verdict rather than raising: a caller that reads an exception as no
policy applied has an open gate, so a raise there is fail-open wearing a
different coat.

**4. Worst case across a composed chain.**

A sequence of individually reversible steps can reach an irreversible outcome no
single step shows. The chain's effective class is the worst case reachable
across it, and the whole chain is gated at that tier from commencement, not step
by step.

**Scope of the chain rule.** The fold takes the worst of the *declared* classes,
which is the ceiling knowable at commencement, before any step has run. Folding
the classes actions actually instantiated once their targets resolved is a
separate, post-execution job and is not implemented here. The two agree when
every step lands at or below its declared class; where they diverge, that
divergence is the finding rather than a defect in either.

**5. A declaration is only as good as its binding.**

A class is a declaration about what an action does. A declaration made against a
contract that has since mutated is not evidence about the action running today.
The model therefore takes an optional second input: whether the declaration is
still bound to the contract it was declared against.

| Binding | Meaning |
|---|---|
| `bound` | The contract the declaration was made against is still in force. |
| `stale` | The contract mutated after the declaration was made. |
| `unobserved` | Not enough independent observation to say either way. |

Three states in the record, two outcomes at the gate. `stale` and `unobserved`
both make a declaration unusable, so both take the same fail-closed path as an
undeclared action. They stay distinct in the record because the binding gap,
declared coverage minus verified coverage, cannot be computed from a binary.

**Absence is not agreement.** `unobserved` is a third state, not a synonym for
`bound`. In a corpus where most entries never change, silence dominates, and
reading silence as conformance manufactures false comfort at exactly the scale
where it matters.

**Observations expire, on a clock rather than a ranking.** A `bound` observation
carries an as-of time and ages out to `unobserved`, not to `stale`: the contract
is not known to have mutated, it is merely no longer known to be current.
Ranking entries by prior drift and re-auditing the top slice cannot substitute
for this, because that ranking exhausts its signal at the carrier fraction and
everything past it is tie-break.

**A chain is as stale as its stalest link.** The worst-case rule that idea 4
applies to classes runs over this axis too.

**Declaration-only is the default.** Where no observation is supplied the model
behaves exactly as it did before this input existed, so results recorded against
an earlier release stay valid and comparable. Supplying no observation is not
the same as supplying `unobserved`: the first says this run has no observation
layer, the second says the layer looked and could not attest.

**What this does not claim.** An observation here is not a witness of execution.
Nothing observes the action running and no runtime effect is compared against
the declared one. The failure modelled is declaration *staleness*, not
declaration *falsity*.

## Oversight and evidence tiers

Oversight rises with the worse of the two axes:

| Oversight | Meaning | Evidence tier |
|---|---|---|
| `unattended` | The agent may run this without a human. | basic |
| `supervised` | Human on the loop, able to intervene. | standard |
| `approval_required` | A human approves before it runs. | enhanced |
| `human_owns` | A named human owns the call. The strongest gate. | highest |

## Mapping to OWASP AISVS v1.0, chapter C9

- **C9.2.3** trusted reversibility classification, from the tool's declared
  effect or policy rather than the model's account, `classify()`.
- **C9.2.4** runtime enforcement by class, `gate()` and `required_oversight()`.
- **C9.2.10** the worst-case reversibility class across a multi-step or
  multi-agent chain, `chain_reversibility()` and `gate_chain()`.
- **C9.5.3** the access-control decision is enforced by policy, never by the
  model itself: these functions are the policy the proposed action is checked
  against, they do not ask the agent what class it thinks applies.

## Usage

```bash
pip install -e ".[test]"
python examples/demo.py     # walk the worked scenarios
pytest                      # run the conformance suite
```

```python
from reversibility import gate, ConsequenceTier

g = gate("non_recoverable", ConsequenceTier.LOW)
print(g.reversibility.name, g.oversight.name, g.evidence_tier)
# IRREVERSIBLE HUMAN_OWNS highest
# low blast radius, still the hard gate, because it cannot be undone
```

## Releases

Verdicts change between releases, so a result only means something against a
named one. That is why every row in `RESULTS.md` carries a suite release and a
commit. Pin a tag rather than following `main`:

```bash
pip install "git+https://github.com/Mayur021/aisvs-c9-action-class-conformance@v1.2.0"
```

`reversibility.__version__` reports the release you are running. The current one
is v1.2.0, which closed four fail-open paths; a verdict recorded against v1.1.1
or earlier does not transfer to it.

## Conformance

An implementation conforms if it satisfies the properties in
`tests/test_conformance.py`:

1. The four classes exist and are ordered.
2. `externally_reversible` gates differently from `reversible`.
3. Unknown or undeclared classes fail closed to the most restrictive.
4. Oversight is monotonic in reversibility.
5. Reversibility and consequence move independently; oversight is the worse of
   the two.
6. A composed chain is gated at its worst-case reachable class from the start.
7. Every worked scenario in `scenarios/scenarios.yaml` resolves as documented.
8. Declaration-only stays the default, and its verdicts are unchanged by the
   observation input existing.
9. Binding has three states in the record and two outcomes at the gate.
10. Absence of an observation is not agreement.
11. Observations expire on a clock, and an as-of ahead of that clock does not
    outrun it.
12. A chain is as stale as its stalest link.
13. The binding gap is computable, and only where observations exist.
14. The package reports one version rather than two.

The scenarios file is the readable contract; the tests are the executable one.

## Status and scope

This is a reference model, not a product. It defines classification and gating
so that enforcement layers, assurance schemas and audit records can key on a
consistent definition. It intentionally says nothing about how authority is
signed, stored or transported; those are enforcement-layer concerns that sit on
top of a correct classification.

Where observation is used, the producer's corroboration threshold lives in that
producer's adapter, outside this repository, so the core holds no
producer-specific semantics and anyone with different telemetry can write their
own adapter against the same vocabulary.

## License

Apache-2.0.


## Real-data fixtures

Seven scenarios in `scenarios/real.yaml` (ids prefixed `real_`) are generated from a measured corpus of the public MCP registry and exercised by `tests/test_real_fixtures.py`. They load alongside the core set; the core suite does not depend on them and runs without both files present. See [FIXTURES.md](FIXTURES.md) for provenance, the annotation-to-class mapping, the install mapping, and known limits.
