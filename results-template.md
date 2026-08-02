# Results: expected vs actual

Record an implementation's actual verdicts against the expected outcomes in `scenario.md`. Copy this file once per implementation under test.

- Suite release: `<tag, e.g. v1.0.1>`
- Suite commit: `<full SHA>`
- Mode: `<declaration-only / declaration plus observation>`
- Implementation under test: `<name and version>`
- Date: `<date>`
- Independent offline check available: `<yes / no, and link>`

| Case                                    | Expected gate decision                                   | Actual verdict | Match | Mechanism | Notes                                   |
|-----------------------------------------|----------------------------------------------------------|----------------|-------|-----------|-----------------------------------------|
| Primary, steps 1 to 2                   | permit unattended                                        |                |       |           |                                         |
| Primary, steps 3 to 5                   | permit supervised                                        |                |       |           |                                         |
| Primary, step 6 (externally reversible) | escalate                                                 |                |       |           |                                         |
| Primary, step 7 (irreversible)          | deny, require human approval                             |                |       |           |                                         |
| Variant A, Model 1 (max of per-step)    | permit-all is the gap                                    |                |       |           |                                         |
| Variant A, Model 2 (composition-aware)  | deny at the threshold-crossing step                      |                |       |           | open research question, see scenario.md |
| Variant B, relabel after signing        | signatures verify, binding fails, fail closed, deny      |                |       |           |                                         |
| Variant C, tail-trim                    | held count below sealed total, fail closed; max survives |                |       |           |                                         |
| Variant D, under-seal, seal alone       | seal alone permits                                       |                |       |           |                                         |
| Variant D, under-seal, reconciliation   | reconciliation flags and attributes                      |                |       |           |                                         |

## Notes

- Record the mechanism for every row. `SHIPPED` where the verdict came from the implementation under test, `ADAPTER` where it came from scaffolding written to make the case testable at all, `NONE` where the implementation has no mechanism and the case cannot be satisfied. A result without this column cannot be read, because shipped behaviour and test scaffolding are indistinguishable in the verdict alone. When asking what an implementation does, discount every `ADAPTER` row.
- Record the suite release and commit. A result is only reproducible if the scenarios it was run against are pinned, and the suite changes between releases.
- The most informative result is Variant A. Whether the gate denies depends on whether the sealing computes worst-case-across-chain (reachability) or only the max of per-step labels.
- Variant A Model 2 is an open research question rather than a conformance bar. No implementation known to the author computes a reachability threshold, including the reference model in this repository.
- For trustless verification, record whether a third party can recompute each verdict offline from the committed bytes and the issuer public key, importing nothing from the implementation under test.
- Where an implementation publishes a public test vector for one of these cases, link it in the Notes column.
