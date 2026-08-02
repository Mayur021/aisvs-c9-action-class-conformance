# Results: expected vs actual

Record an implementation's actual verdicts against the expected outcomes in `scenario.md`. Copy this file once per implementation under test.

- Suite release: `<tag, e.g. v1.0.0>`
- Suite commit: `<full SHA>`
- Mode: `<declaration-only / declaration plus observation>`
- Implementation under test: `<name and version>`
- Date: `<date>`
- Independent offline check available: `<yes / no, and link>`

| Case                                    | Expected gate decision                                                         | Actual verdict | Match | Notes                                            |
|-----------------------------------------|--------------------------------------------------------------------------------|----------------|-------|--------------------------------------------------|
| Primary, steps 1 to 5                   | permit unattended                                                              |                |       |                                                  |
| Primary, step 6 (externally reversible) | escalate                                                                       |                |       |                                                  |
| Primary, step 7 (irreversible)          | deny, require human approval                                                   |                |       |                                                  |
| Variant A, composition                  | deny at the threshold-crossing step (Model 2); permit-all is the gap (Model 1) |                |       | which sealing model does the implementation use? |
| Variant B, relabel after signing        | signatures verify, binding fails, fail closed, deny                            |                |       |                                                  |
| Variant C, tail-trim                    | held count below sealed total, fail closed; max survives                       |                |       |                                                  |
| Variant D, under-seal                   | seal alone permits; reconciliation flags and attributes                        |                |       |                                                  |

## Notes

- Record the suite release and commit. A result is only reproducible if the scenarios it was run against are pinned, and the suite changes between releases.
- The most informative result is Variant A. Whether the gate denies depends on whether the sealing computes worst-case-across-chain (reachability) or only the max of per-step labels.
- For trustless verification, record whether a third party can recompute each verdict offline from the committed bytes and the issuer public key, importing nothing from the implementation under test.
- Where an implementation publishes a public test vector for one of these cases, link it in the Notes column.
