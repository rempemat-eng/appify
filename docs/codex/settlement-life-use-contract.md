# Settlement-life explicit-use interface

MyGame · slot=editor-data · X3-explicit-use/r1 · ASSIGN6477734909 · lead brief6477267855.

## Interface proposal, before production edits

Extend PR332 at `df386f8939bb3854390b9e519351b847a7d5fb3c`; do not replace its checker. PR340 `d2012e572b36d12a81ec447d1aabb3ee90b3b53d` audits the actual303 source `4984438d09b5fe1333d3e6ea6e6ee82be2bdc908`: Canalside b003/b009 have occupational labels without a residence; Fernhollow b002/b005 explicitly say the shopkeeper lives above. These observations are not new resident assignments.

`check(plan, source, *, source_pin=None, use_contract=None)` receives the trusted classification separately from the packet, just as it receives the trusted source separately. The validator never derives classification from `occupants`, type names, substring/NLP rules, or a packet's own claimed policy. Source and classification remain separate trust inputs. A caller who controls both expected inputs is an author/reviewer, not an untrusted packet submitter.

The proposed external JSON contract has exactly these top-level fields:

- `schema: "mygame.settlement_use/1"`;
- `source: {commit, blob, path}`, exactly equal to the independently selected town SourcePin;
- `buildings`: one record per source building, with unique `id`, independent `home` and `work` axes (`true`, `false` or `null`), and `evidence` records `{field, text}` matching exact nonempty source `purpose` or `occupants` text;
- `workplaces`: one record per explicitly residential building `{home, workplace}`, where workplace is an explicitly working building ID or null (deferred). A binding must be separately authored; a worker's occupation does not select a job site. A mixed-use shop may explicitly bind to itself. This is not an employment count.

True means explicitly supported; false means explicitly excluded, not merely absent from the text. Null means unknown. For example a workshop can have `work=true, home=null`; it is not silently converted into work-only. No current audited building is declared explicitly non-residential by this proposal. Exact text matching proves evidence provenance, not the correctness of an author's interpretation; review remains necessary. Contract input does not grant plan approval.

The CLI adds an all-or-none `--uses`, `--uses-commit`, `--uses-blob`, `--uses-path` group. Expected identity is supplied by the caller, never read from the town packet. It verifies the contract's exact Git blob bytes and commit:path mapping before strict JSON parsing, then verifies its embedded town-source identity. Contract paths are safe repository-relative JSON paths with no empty/dot/traversal components. No new source contract JSON or real town data is committed in this scope; examples and adversarial controls live in the existing test module. A receiving authoring task must publish/review an actual pinned contract before another real town packet can pass.

Coverage requires exactly one provisional representative for each `home=true` record. Home-null occupied records remain unassigned and produce an explicit incomplete-coverage finding/CLI EXIT1; assigning them as homes does not remove the finding and is rejected. Missing classifications, duplicate IDs, wrong source/evidence, malformed axes and invalid bindings are invalid input/EXIT2. Contract rows must cover all source building IDs exactly; unknowns cannot disappear by omitting rows.

Resident roles and source occupants still come from their explicit home, and district, placeholder names, proposal status, deferred animals/props/headcount and all non-life town bytes remain protected. A supplied workplace must equal the separately authored binding and have `work=true`; null stays deferred. Existing home/street provisional routines remain unchanged; workplace references do not invent commute, job schedules or a production clock.

Compatibility is deliberately narrow: the original default Gullwick SourcePin and its all-residential packet retain the legacy behavior and existing CLI0/1/2 controls. Other source identities need an external use contract, including arbitrary-town diagnostics that formerly treated all occupied buildings as homes. Those old diagnostics will be updated to expect explicit-contract incompleteness while retaining all source/no-drift/refusal checks. A packet cannot request legacy mode by changing its own provenance. Current-source Gullwick may use an explicitly reviewed contract; old-base passes do not validate combined source.

## Required regressions and boundaries

Keep the original legacy/source identity/malformed/reference tests. Add actual source-pinned Canalside unknown workshops, explicit Fernhollow mixed shop/self-work, synthetic explicitly work-only data, tampered/missing/duplicate use rows, strict boolean/null axes, wrong-source/exact-text evidence, unauthorized workplace bindings, packet-owned policy substitution, partial CLI options and changed contract bytes. Confirm malformed inputs fail without traceback or input mutation. Unknowns must never produce a complete/PASS packet. No names, headcounts, roles, routines, geometry, schema/package/Player or runtime changes are authorized.

Production edits follow publication of this proposal to the lead. Full final verify/art and matching hosted checks remain required; focused tests alone do not make this draft ready. Heavy validation waits for the lead's actual serial slot/headroom. This child inherits unapproved330/303 ancestry; lead must integrate only reviewed engineering changes without carrying those foundations into main. Matt retains art/map acceptance. This document is an interface proposal, not a finished implementation or complete X3 packet.
