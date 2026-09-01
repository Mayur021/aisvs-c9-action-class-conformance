# Real-data fixtures - provenance, mapping, and limits

Seven scenario fixtures in `scenarios/real.yaml` (ids prefixed `real_`) are built
from real, confirmed, pseudonymized records of the public MCP registry, measured over
35 crawl observations (2026-06-09 to 2026-08-01, 44,172 tools on reachable
servers; declared-vs-verified binding gap 24.46 percentage points). Four pytest
regression tests (two fail-open families) cover the behaviors flagged during the
observation-input review; all four are fixed as of v1.2.0 and the tests are now
permanent guards rather than expected failures. Every fixture
is generated from the published dataset by a deterministic generator - no literal is
hand-typed, and anyone holding the dataset reproduces the selection exactly.

**Data:** MCP Declared-Effect Coverage and Contract Binding v1, (c) Gautam Bharti,
CC-BY-4.0, Zenodo DOI 10.5281/zenodo.21778282 (version DOI). This section is the
supplied form of the required attribution; the dataset files are additionally pinned
by the integrity digests below. Related dataset: MCP Registry Drift Panel v1,
DOI 10.5281/zenodo.21751273 (version DOI; shares the pseudonym token space).

## File integrity

```
ad14b54afb47a82deef9fe7a3a72e59aed450e439ce1c9a03785f50550e3baa9  binding_states_v1.csv
7bcc2475e27d9c0eb4982d058dd6a342c5ad96257ff8e80ad89df3677e49eddd  flips_v1.csv
36266d02957dca37adea910c7ac0922ee90dda554cd638802833df1040b0d2fd  declared_vectors_v1.csv
585e7752c7e0848cb91a4e340375e7f3215369717cd432f16d88bcbd05b711e0  tool_observation_spans_v1.csv
da0d97d84fbf134f37bfd89ff463515f46453b442fa1543603852a9a875559e7  rq1_series.csv
77ae93be0b8ee34f3badb3dc6e6387e61214a57eac3d703f44e77ea9a5609e62  results.json
ce8f8751196784959413c1e1c2f61df945843e254e19fe3e3b0c0fafd92fe3e9  DATASET_CARD.md
7eb9ab39c1d262bf84188212942015cf9b4c3bbfdff33313b4e7f0a44a4b772f  REPORT.md
881986feae926aa04f90ab1301d99ea8ea2790fc59b3aed6ee0c0d05a17889ac  build_fixtures.py
8d3382c3c74195a4c1dc91e4a4d37c6a38ab60dff63335b0b52585eb5eda5731  verify_deposit.py
```

## The mapping: MCP effect annotations -> declared_effect

Canonical hints: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`.
Evaluation is FIRST-MATCH, top to bottom. Evaluation is THREE-VALUED: each hint is
`true`, `false`, or ABSENT. MCP-spec default values are NOT applied - an absent hint
stays absent, an equality condition on an absent hint evaluates false, and a negated
condition is the logical negation of the equality (`x != true` is TRUE when `x` is
absent). Fabricating a declared value the server never made would break provenance; the
catch-all row already lands every partial vector in `null`, which the suite fails
closed - equally fail-closed, strictly more honest about what was declared.

| Condition | declared_effect |
|---|---|
| `destructiveHint == true` | `non_recoverable` |
| `readOnlyHint == true` (and destructiveHint != true) | `read_only` |
| `destructiveHint == false` and `openWorldHint == true` | `externally_recoverable` |
| `destructiveHint == false` and `openWorldHint == false` | `recoverable_local` |
| no canonical hint present | `null` (undeclared - fails closed) |
| any other combination | `null` + finding: partial/underdetermined declaration |

The table is total over `{true, false, absent}^4` under top-to-bottom evaluation.
Worked examples: `{openWorldHint: true}` alone lands in the catch-all;
`{readOnlyHint: true}` alone lands in row 2 (destructiveHint absent, so
`destructiveHint != true` evaluates TRUE); the common web-search vector
`{readOnlyHint: true, destructiveHint: false, openWorldHint: true}` lands in row 2
under first-match. `idempotentHint` never affects `declared_effect` - it participates
only in flip-direction analysis; implementers must not invent a mapping for it.

A bare `{readOnlyHint: true}` reaches the most permissive class by design - this
mapping READS declarations, it does not trust them. The observation/binding plane is
the control: never gate on this table's output without a BOUND observation.

Conflict rule: `readOnlyHint == true` AND `destructiveHint == true` (both explicitly
declared) -> `non_recoverable` plus a finding (self-contradictory declaration). In a
pure first-match implementation the finding is a side channel of row-1 evaluation - a
vector-to-class function alone silently drops it.

The suite additionally recognizes `externally_visible` as a declared effect (mapped to
IRREVERSIBLE); no MCP annotation vector maps to it under this table, which is why it
does not appear above.

## Consequence derivation (adapter defaults, overridable)

Rows can co-fire; multiple matches resolve worst-wins (CRITICAL > HIGH > MEDIUM > LOW) -
contrast the annotation mapping above, which is first-match. A record with NO receipt
plane (drift telemetry only) evaluates `side_effect_class` and `egress` as `none` for
this table, so the change-kind terms alone determine its tier; a PARTIAL receipt-plane
record evaluates each absent field per equality-on-absent and lands in the fail-closed
default where no row matches. Adapters map their own telemetry onto the closed
vocabularies explicitly (`side_effect_class` in {none, local-write, outbound,
destructive}; `egress` in {none, internal, external}); never invent per-field
defaults. Binding-plane fixtures (F1-F7) carry none of these inputs, so their
consequence derives from the mapped class: read_only->LOW, recoverable_local->MEDIUM,
externally_recoverable->HIGH, non_recoverable->CRITICAL, null->CRITICAL.

| Source signals | consequence |
|---|---|
| `side_effect_class == destructive` OR change-kind in {tool-removed, annotation-flip-to-destructive, deep-schema-undiffable} | CRITICAL |
| `egress == external` OR `side_effect_class == outbound` OR breaking-schema change-kind (removed-param, type-changed, enum-values-removed, constraint-narrowed, required-set-expanded, added-required-param, output-schema-changed) | HIGH |
| `side_effect_class == local-write` OR output-schema-added | MEDIUM (output-schema-added is a deliberate elevation above its non-breaking source status: new output surface downstream consumers may act on) |
| `side_effect_class == none` AND `egress` in {none, internal} AND (no change-kind, or cosmetic change-kind: description-only, added-optional-param, tool-added) | LOW |
| anything not listed | HIGH (default - fails closed) |

LOW-row caveat (normative): consequence measures ACTION blast radius, not
instruction-injection risk. `description-only` is the canonical tool-poisoning
channel and `tool-added` can introduce an attack surface wholesale - LOW here must
never be read as benign. The defense is on the binding plane: the contract hash
includes the description, so a description-only mutation trips staleness and fails
closed - `real_stale_contract_mutation`'s exact shape.

## Fixture provenance

Reference date for `age_days` values: 2026-08-01 (the final observation), with one
stated exception - `real_bound_aged_out` models the state at the first post-gap
observation (2026-07-10), the instant its real aging story occurred; its provenance
entry says so. `age_days = floor((reference_date - observed_as_of) / 86400s)`,
computed at day granularity. The floor makes the bridge permissive by up to one day
at the boundary; a ceiling is the fail-closed alternative at day granularity. Third
parties applying this bridge to their own telemetry set the reference date to their
corpus's latest observation and apply the same rule.

### `real_bound_readonly_tool`

- **Source:** binding_states_v1.csv + declared_vectors_v1.csv + tool_observation_spans_v1.csv
- **Record:** `004a96c25250baf5/5cd24987d462b79b`
- **Corroboration:** n_obs=35, contract_changes=0, decl_changes=0
- **What a pass does NOT prove:** Does not test runtime behavior - contract/declaration staleness only. A pass does not prove the tool is safe, only that its declaration is current and bound.
- **What a FAIL means for your fleet:** A FAIL means your gate blocks even long-stable, fully-attested read-only tools - the false-positive floor of your fleet.

### `real_stale_contract_mutation`

- **Source:** binding_states_v1.csv + declared_vectors_v1.csv
- **Record:** `00396363428beb60/1b4f3a57bea9d5b7`
- **Corroboration:** n_obs=35, contract_changes=2, decl_changes=0
- **What a pass does NOT prove:** Covers contract mutation under a stable declaration (staleness, not falsity). Does not observe what the mutated tool actually does.
- **What a FAIL means for your fleet:** A FAIL means your gate honors declarations whose underlying contract has verifiably changed - the exact channel a description rewrite (rug-pull) uses.

### `real_bound_aged_out`

- **Source:** binding_states_v1.csv + tool_observation_spans_v1.csv
- **Record:** `315e208beba99f95/0062985cae8f3503`
- **Corroboration:** n_obs=15, last pre-gap confirmation 24 days before the first post-gap observation
- **What a pass does NOT prove:** Models the state at the first post-gap observation (2026-07-11), NOT the tool's end-of-corpus state, which re-bound once crawls resumed - the aging clock, not a mutation (ages to UNOBSERVED, not STALE).
- **What a FAIL means for your fleet:** A FAIL means your gate honors attestations unrefreshed across a multi-week observation outage - trust that outlives its evidence.

### `real_unobserved_declared_tool`

- **Source:** binding_states_v1.csv + declared_vectors_v1.csv + results.json
- **Record:** `1d3fc6a852fcd612/d5d0025a871f69be`
- **Corroboration:** n_obs=2 (below the K_MIN=3 floor by construction)
- **What a pass does NOT prove:** Instantiates under-observation silence (below the corroboration floor), NOT the never-changed/bound silence share - the two silences are different populations.
- **What a FAIL means for your fleet:** A FAIL means unattested tools inherit trust from their own declarations - silence read as verification, at the scale where most of a real corpus is silent.

### `real_flip_restrictive_state_only`

- **Source:** flips_v1.csv + declared_vectors_v1.csv
- **Record:** `f7576245a2266efd/4f5b438c4667c3c8 (openWorldHint false->true, days 20260609->20260714)`
- **Corroboration:** decl_confirm_count=19
- **What a pass does NOT prove:** Asserts the post-supersession STATE only; the flip EVENT and finding channel are not expressible in the scenario schema (misfit M1).
- **What a FAIL means for your fleet:** A FAIL means a tool that re-labels itself keeps the trust earned under its previous label - observations surviving a declaration change they were never made against.

### `real_flip_permissive_state_only`

- **Source:** flips_v1.csv + declared_vectors_v1.csv
- **Record:** `7db11cce30d8579e/379e7ff3d2df41a1 (destructiveHint true->false, days 20260609->20260610, mode=primary)`
- **Corroboration:** decl_confirm_count=33; one of 17 confirmed permissive destructiveHint flips in this corpus (see M6 for what confirmed means here)
- **What a pass does NOT prove:** A pass proves the post-flip STATE fails closed, NOT that permissive-flip findings are detected - the finding channel is untestable in this schema (misfit M1); the _state_only suffix carries that caveat.
- **What a FAIL means for your fleet:** A FAIL means a tool can silence its own danger label and keep its standing - the cheapest possible attack on a declaration-gated fleet.

### `real_chain_stalest_link`

- **Source:** binding_states_v1.csv + declared_vectors_v1.csv + tool_observation_spans_v1.csv
- **Record:** `server 004a96c25250baf5, tools 00b77a59bda27096/3a5ca66645425f9d/252e682e3716563d`
- **Corroboration:** n_obs=35/35/35
- **What a pass does NOT prove:** Tests binding-axis chain composition only; no policy is attached, so BOUND-link ages are informational and do not age out within this scenario.
- **What a FAIL means for your fleet:** A FAIL means one compromised link in a workflow inherits the trust of its clean neighbors - chains graded by their best step instead of their worst.


## Regression guards (F8/F9) - operational reading

**Fixed in v1.2.0.** Through v1.1.1 the suite failed OPEN on unspecified-consequence
and unhashable-effect inputs: a chain step carrying no consequence resolved to the
weakest tier rather than being treated as unaccounted, and an unhashable declared
effect raised out of the decision path instead of returning a verdict. Both now
resolve to the strongest tier and to IRREVERSIBLE respectively. The xfail markers
were strict, so the fix made all four XPASS and reddened CI, and the markers came
off in the same commit. They are ordinary tests now.

v1.2.0 closes two further fail-open paths on the same axis, found by audit rather
than by the observation-input review. An observation whose as-of lies in the future
produced a negative age that no maximum age can exceed, so it never aged out at any
policy; it now fails closed to UNOBSERVED regardless of the expiry policy. And a
naive timestamp on either the observation or the policy clock raised TypeError from
the decision path, which a caller treating an exception as no-policy-applied would
read as an open gate; both are now refused at construction. Guards for all four live
in tests/test_conformance.py under properties 11 and 14.

Results-table authors: which tag you ran matters here, so name it.

> Suite v1.2.0 or later: no known fail-open paths recorded against the suite.
> Suite v1.1.1 or earlier: fails open on unspecified-consequence, unhashable-effect,
> future-dated-observation and naive-timestamp inputs; see FIXTURES.md.

Results tables built on these fixtures inherit the SHIPPED/ADAPTER/NONE mechanism
column; any mapping scaffolding a third party writes to run them counts as ADAPTER.

## Known limits (recorded, not massaged)

- **M1 - the event channel is untestable here.** The scenario schema has no slot for
  flip EVENTS or FINDINGS; the flip fixtures assert the resulting state only. The
  `_state_only` id suffix carries that caveat into every results table.
- **M2 - the corroboration/reversibility join is authored, not observed.** No single
  mcpindex record carries both; the fixtures join them via the mapping above, and this
  document says so.
- **M3 - age values are frozen to the generation date** via the fixed reference date.
- **M4 - direction asymmetry.** The incident taxonomy has a kind only for the
  restrictive flip direction; permissive-direction flips (the silencing shape) are
  visible only in the flips dataset. idempotentHint flips are class-invariant under
  the mapping and outside supersession semantics entirely.
- **M5 - LOW is not benign** (see the LOW-row caveat above).
- **M6 - "confirmed" here is repeated observation by ONE crawler, not independent
  corroboration.** The deposit states the bound itself, in `results.json`:
  "confirmations are repeated crawls by one crawler; independent-observer corroboration
  applies to the receipt network, not this baseline series." Every `decl_confirm_count`
  and `n_obs` in this document is confirmation at that strength, including the 17
  permissive destructiveHint flips, each confirmed between 17 and 33 times. Do not
  describe these fixtures as independently corroborated. Raised by avp9-nexus in review
  on GenAI-Security-Project/agent-control-standard#38, against wording that had used
  the stronger word in this file and in three other places.

## Scope

Contract/declaration staleness only. Nothing here observes runtime behavior; no
action is ever witnessed executing. A declaration made against a contract that has
since mutated is not evidence about the action running today - measuring how often
that happens is what this dataset is for.

## Regeneration

Both scripts ship inside the dataset record (10.5281/zenodo.21778282). From a flat
download of the record:

    python3 verify_deposit.py    # every aggregate reproduces from the per-tool files
    python3 build_fixtures.py    # emits this file, the scenario block, and the tests

The verifier recomputes results.json from the released CSVs and fails on any
mismatch. The generator consumes only the record's files, applies the documented
selection predicates with total-order tie-breaks, and reproduces these fixtures
byte-identically.

### Install mapping

The generator emits a scenario block and a test module. It does not, and cannot,
know where a consumer installs them - a second consumer may lay them out
differently, so a path baked into the generator's output would be wrong for
someone. The generator's own prose therefore refers to its emitted filenames, and
the mapping into this repository is recorded here:

| Generator output | Installed in this repository as |
|---|---|
| `scenarios_block.yaml` | `scenarios/real.yaml` |
| `test_real_fixtures_regressions.py` | `tests/test_real_fixtures_regressions.py` |
| `FIXTURES.md` | `FIXTURES.md` (this file, with this section appended) |

The dataset digests above are unaffected: they pin the record's files, and
`build_fixtures.py` is unchanged. Re-running the generator against the record
reproduces the block byte-identically; only where it lands is local.
