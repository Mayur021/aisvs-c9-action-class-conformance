# Independent conformance results

Runs of this suite against real implementations, recorded so they can be found and compared. Each entry names the release the run was pinned to and a hash of the published artifact, so a reader can confirm they are looking at the result that was recorded rather than a later revision.

## How this list works

Results are published and hosted by the implementer, not by this repository. This file links to them. That separation is deliberate: the author of a conformance suite should not also be the publisher of claims made with it.

**Listing is not endorsement, and it is not verification.** No entry here has been independently checked by the suite author. Each result is self-reported by the party that ran it, and every entry says so.

**Products of the suite author's employer are not listed.** They are welcome to run the suite and publish like anyone else, but they will not appear in an index the author maintains.

To add an entry, publish the filled results template somewhere durable, then open a pull request adding a row below with the release, the date, a link, and a SHA-256 of the published artifact.

## Runs

| Implementation | Suite release | Date | Result | SHA-256 | Self-reported |
|---|---|---|---|---|---|
| [Shango MID](https://doi.org/10.5281/zenodo.21759078) | v1.0.0 (`50d0571`) | 2026-08-02 | 12 / 14 matched · 1 divergence (recorded as an open research question) · 1 n/a | `86e2db073d20ed583b0ecb25ab27a16a4ac545251e5fff22ec7780c09a6437d1` — `Shango_AISVS_C9_Scenario_Results_v1.0.0.pdf` | Yes |

## Reading a result

Check three things before drawing a conclusion from any row.

Which release it was pinned to. The suite changes, and a verdict against one release does not transfer to another.

The mechanism column in the result itself. A verdict from scaffolding written to make a case testable says nothing about what the implementation ships. Discount every `ADAPTER` row when asking what a product does.

Whether a third party can re-run it. A result nobody outside the implementer can reproduce is a report, not evidence.
