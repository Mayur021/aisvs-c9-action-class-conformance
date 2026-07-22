# Reversibility-graded action-class authority: reference implementation

A small, dependency-light reference model and conformance suite for grading how
much oversight an agent's action needs by how hard that action is to undo. It
implements the classification and gating primitives behind OWASP AISVS v1.0
chapter C9 (Orchestration & Agentic Action Security), so an implementation can
be checked against a single, explicit definition rather than each one inventing
its own.

The point it makes concrete: a completed check is evidence of what was looked
at, not authority to act. Whether an action may run unattended, or must be owned
by a named human, follows from the class of the action, evaluated outside the
model that proposed it.

## The model in four ideas

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

**4. Worst case across a composed chain.**

A sequence of individually reversible steps can reach an irreversible outcome no
single step shows. The chain's effective class is the worst case reachable
across it, and the whole chain is gated at that tier from commencement, not step
by step.

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

The scenarios file is the readable contract; the tests are the executable one.

## Status and scope

This is a reference model, not a product. It defines classification and gating
so that enforcement layers, assurance schemas and audit records can key on a
consistent definition. It intentionally says nothing about how authority is
signed, stored or transported; those are enforcement-layer concerns that sit on
top of a correct classification.

## License

Apache-2.0.
