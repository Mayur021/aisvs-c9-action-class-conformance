# Independent conformance results

Runs of this suite against real implementations, recorded so they can be found and compared. Each entry names the release the run was pinned to and a hash of the published artifact, so a reader can confirm they are looking at the result that was recorded rather than a later revision.

## How this list works

Results are published and hosted by the implementer, not by this repository. This file links to them. That separation is deliberate: the author of a conformance suite should not also be the publisher of claims made with it.

**Listing is not endorsement, and it is not verification of a result.** Two things are worth keeping apart. Before a row is merged the artifact is checked: the link resolves, and the digest matches the bytes it names. That is so a reader can be sure they are holding the file the row points at. The result inside that file is not checked by the suite author, and no row here carries a verdict the author produced. Each result is self-reported by the party that ran it.

**Products of the suite author's employer are not listed.** They are welcome to run the suite and publish like anyone else, but they will not appear in an index the author maintains.

To add an entry, publish the filled results template somewhere a reader can fetch it unchanged, then open a pull request adding a row below with the release, the date, a link, where the run happened, and a SHA-256 of the published artifact together with the filename that digest belongs to.

Every row states where its verdicts came from, by case: how many came from the behaviour the implementation ships, how many from scaffolding written to make a case testable, and how many had no mechanism at all. The names your own report uses for those categories do not matter, only the counts. Give it by case rather than by table row, since a row can carry several cases. Where a run did not record this, the cell reads "mechanism not reported" rather than being left empty, because an empty cell reads as though everything came from shipped behaviour, which is the flattering reading and not one the index should hand out for free.

Any link that resolves to fixed bytes works. A version DOI, a release asset, a permalink pinned to a commit, or a file on your own site are all fine, because the digest is what proves a reader is holding what you recorded rather than something published later. What does not work is a link that resolves to whatever is newest, a Zenodo concept DOI being the common case, since the bytes behind it change and an indexed digest stops matching without anything appearing to be wrong. Where a deposit carries more than one file, name the file the digest belongs to, because a hash on its own does not say which artifact it pins.

## Runs

| Implementation | Suite release | Date | Result | Self-reported | Re-runnable | Run origin | Artifact | SHA-256 |
|---|---|---|---|---|---|---|---|---|
| [Shango MID](https://doi.org/10.5281/zenodo.21759078) | v1.0.0 (`50d05718828cc1e18611dd0cda1bd03084ccbb6f`) | 2026-08-02 | 12 / 14 matched · 1 divergence (recorded as an open research question) · 1 n/a · mechanism by case: 9 shipped, 4 adapter, 1 none | Yes | No, runner closed | not recorded | `Shango_AISVS_C9_Scenario_Results_v1.0.0.pdf` | `86e2db073d20ed583b0ecb25ab27a16a4ac545251e5fff22ec7780c09a6437d1` |

**Result** carries separate counts rather than a single ratio: how many cases matched, how many diverged, and how many could not be evaluated. A case with no mechanism to exercise it has not failed, and a ratio settles that question silently by putting it in the numerator or the denominator. The row is the part that gets quoted, so a distinction the per-case rows preserve is lost at exactly the point it travels furthest. The mechanism split rides in the same cell for the same reason. A reader who quotes the count without it has quoted a number the result itself qualifies.

**Self-reported** is yes on every row, by design: the index carries no result the suite author produced.

**Re-runnable** says whether someone outside the implementer can execute the run themselves. A result nobody else can reproduce is a report rather than evidence, and that limit belongs in the index rather than only inside the linked document.

**Run origin** says where the run was executed and whether that environment still exists. It is free text rather than a fixed set of options, because a closed list makes an honest respondent round to the nearest available answer, and that rounding is invisible and runs in the flattering direction every time. Where the environment no longer exists, the cell says so. A row added before this column existed reads "not recorded" rather than being left empty. The point about closed answer sets is Ishaan Ghosh's, made against his own record.

**Artifact** names the file each digest pins, since a deposit can carry more than one file and a hash on its own does not say which.

## Reading a result

Check four things before drawing a conclusion from any row.

Which release it was pinned to. The suite changes, and a verdict against one release does not transfer to another.

The mechanism split. The Result cell carries the totals; which specific cases were adapter-borne is in the linked document. A verdict from scaffolding written to make a case testable says nothing about what the implementation ships. Discount the adapter-borne cases when asking what a product does.

Whether a third party can re-run it. A result nobody outside the implementer can reproduce is a report, not evidence.

Where the run happened. An environment that no longer exists cannot be inspected by anyone, including the party that ran it, and a row that does not say reads as though it could be.
