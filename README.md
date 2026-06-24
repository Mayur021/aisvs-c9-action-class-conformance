# AISVS C9 Action-Class Conformance Scenario

An independent, vendor-neutral conformance scenario for the action-class and reversibility controls in the OWASP Artificial Intelligence Security Verification Standard (AISVS) v1.0, chapter C9, Orchestration and Agentic Security.

It hands an enforce-by-class gate a concrete multi-step agent action chain plus four adversarial variants, each with the expected gate decision, so any implementation can be checked against the same cases.

## Scope

The scenario exercises these AISVS v1.0 C9 controls:

- C9.2.3, reversibility classification of high-impact actions (read-only, reversible, externally reversible, irreversible)
- C9.2.4, runtime enforcement keyed to that classification
- C9.2.8, approvals cryptographically bound to action parameters, identity, context, and a single-use nonce (exercised by the relabel-after-signing variant)
- C9.2.10, worst-case reversibility class across a multi-step or multi-agent chain
- C9.2.1, human approval for irreversible actions

## Contents

- `scenario.md`, the conformance scenario: a primary action chain and four adversarial variants (composition, relabel-after-signing, tail-trim, dishonest under-seal), each with expected gate decisions and a test assertion.
- `results-template.md`, a template for recording an implementation's actual verdicts against the expected outcomes.

## How to use

1. Read `scenario.md`.
2. Run the primary chain and each variant against your enforce-by-class gate.
3. Record actual verdicts in a copy of `results-template.md`, alongside the expected outcomes.
4. The interesting findings are the divergences, especially Variant A (composition), where per-step classification and worst-case-across-chain can disagree.

## Status and provenance

This is independent work by Mayur Agnihotri, a contributor to OWASP AISVS. It is not an official OWASP or AISVS artifact and does not speak for the AISVS project. It is a community conformance scenario for the C9 controls, offered for anyone building or verifying an enforce-by-class gate.

The scenario grew out of a public discussion in the CoSAI Workstream 4 secure-design issue tracker on sealed worst-case classification and held-set-alone verification.

## Vendor-neutral

The scenario is implementation-neutral. It names no products and assumes no particular gate. Where an implementation publishes verifiable test vectors for one of these cases, a link can be added under results.

## License

Apache License 2.0. See `LICENSE`.
