# Y15: partial town-authoring interface

Status: **draft partial interface; proposals are off by default**.
Lead [scope 6477625392](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6477625392)
narrows this deliverable to the explicit, fail-closed representation interface.
Successful historical regeneration/adoption is not delivered.
No town placement, terrain change, raster art or merge is approved. Matt reviews
the proposals; the Codex lead owns integration. Slot `forge`, task
`Y15-generator/r1`, [claim 6476103625](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6476103625),
[exporter scope 6476229742](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6476229742).

The branch starts at map #303 `4984438d09b5fe1333d3e6ea6e6ee82be2bdc908`
and takes unchanged #331 `96215d5b1d6f395e4aa4fbdac207ff6a4ef384d3` as a
dependency. Its Highgarth form descriptions, ordinary trade-cycle advancement,
landmark description and six regression methods remain intact.

## Inputs and boundary

| Proposal | Exact commit | Additions | Proposed counted total |
|---|---|---|---:|
| Cinderwick #334 | `4669140421d7d8c69482fc90b78fea0a50d1d4bc` | two cottages, two uncounted net sheds, named work aprons | 15 |
| Hearthold #335 | `59f3722d1b39050cc81709fa5933d4c9c093ee98` | two detached homes and one workshop | 31 |
| Launch Cape #336 | `9276174000e47858e92a25803e606fb9dea1fc87` | two staff cottages, one workshop, staff-homes district | 6 |

The authoring constants in `towns55.PROPOSED_ADOPTIONS` contain the exact full
commit/blob/path identities for each proposal and its #303 baseline. Their data
comes from those authored proposals. Regeneration never reads its generated
town JSON as an input. The committed JSON files are read only as test oracles.

The actual producer entrypoints `lay_all`, `hearthold` and `launch_cape` now
have keyword-only `authored=None` inputs. Ordinary `geo55` is unchanged: its
existing calls select no packets, read no proposed packet and add no proposed
geometry. `lay_all` accepts only `cinderwick`/`hearthold` keys and forwards only
the Hearthold selection; standalone Hearthold/Cape accept only their own key.
Unknown keys and wrong source/target towns are rejected before terrain work.
Deliberate callers can pass, for example,
`authored={'hearthold': PROPOSED_ADOPTIONS['hearthold']}`. This remains an
unapproved proposal and can fail on actual ground. No environment flag or
implicit global activation enables it.

Earlier draft checkpoints wired the proposal constants into ordinary factories.
That automatic activation was removed during the lead's scope review; it is
not retained as the default behavior or credited as successful regeneration.

`Town.adopt(packet)` validates the packet and places its existing documented
forms through `Town.hand`. Before placement it checks actual terrain kinds,
existing uses, barriers, tier agreement, exact rear plots and mutual clearance.
It keeps prescribed IDs, doors and street references as explicit authoring
data. Existing plot rectangles and named field/yard uses are reserved explicitly,
including previously laid towns; ordinary `used` padding is not a reservation.
Rear plots must fit the selected terrain window, and authored door approaches
honour the real off-street barrier mask. The old `put()` raw-record cap predates landmark exclusion: authored
capacity uses the existing exported counting convention instead, followed by
the unchanged town checker. This permits nine Launch Cape records with six
counted buildings, without counting its landmarks as houses or changing a guide.

`town_plans` consumes this optional channel explicitly. The ordinary layout,
access and counting pipeline stays in place. It rejects ambiguous or unmatched
building/district identities, conflicting geometry, missing streets, unreachable
authored doors, clipped terrain windows and failed existing town checks. It
recomputes building totals, front totals, district membership and footprint.
Source-authored district descriptions remain descriptions rather than a new
population or workplace inference. The source-requested terrain window must
contain the actual footprint; it cannot hide out-of-bounds placement.

With no authored packet, all 21 record exports remain byte-identical to the
unchanged #331 exporter on the documented fixture inputs. Default factory
source/wiring controls also compare all three complete geometry bodies against
#331 after specialising only the explicit empty authoring selection; unchanged
`geo55.py` bytes are checked. These are bounded source controls, not a second
raw-world run. Nothing changes another town's defaults or interprets
the descriptive source roles as individually authored residents or routines.

## Cinderwick terrain ambiguity retained

The pinned baseline and proposal both encode route ground at cells
`(312, 730)`, `(311, 731)` and `(312, 731)`, inside proposed
`cinderwick-b015`'s `[306, 727, 7, 5]` footprint. The existing exported street-band
check does not cover those three route-painted cells. The inherited test fixture
reconstructs every `r` as `road`, which placement correctly refuses. That is a
lossy reconstruction: the raw generator also has other route kinds, including
`trail`, whose buildable classification differs. The raw terrain kind, street
mask and actual `Town.hand` oracle must therefore be inspected before declaring
a real placement fault or changing a checker rule. This branch does not erase
route paint, move the cottage, change its dimensions or grant an exception.

The direct town checker passing the proposal and the lossy fixture refusal are
both insufficient evidence of actual placement. Real tier and access mismatches stay
failures. Any future correction must replace its source pin explicitly and rerun
preservation checks; there is no silent refresh to a newer town document.

### Instrumented diagnostic and historical reproducibility blocker

The lead authorised one **cache-lifetime-instrumented numeric diagnostic**,
after two resource-limited attempts. Pinned #331 generator/exporter bytes and
the five unchanged geo producer blobs were checked before and after. An
oracle-side four-entry cache retained the existing `geo5.noise` arithmetic:
its RNG is local and seeded, cache consumers only get/set/clear, and `set_dims`
clears it after dimension changes. Inserted arrays were read-only; the mutation
control refused its write, no producer attempted a cached-array mutation, and an evicted key's
recomputation was bit-identical (SHA-256
`078539c2379847c0f30ecada89271edbaf2c9d0fa205d9890540b853bc12e943`).
No cache optimisation or terrain change is included in production source.

The diagnostic exited 0 after 380.95 seconds at 1,626,324,992 bytes peak RSS;
OOM counters stayed zero. Cache epochs changed from 864×1408 to 896×1568,
with 530 insertions and 518 evictions. It stopped after baseline Cinderwick,
before the next town or exporter. In **that run**, the three cells were `path`,
with no taken/street/barrier/keepout mask, and the whole footprint was tier 6.
The exact original `Town.hand` call returned false; the recorded footprint
kinds, masks and building count remained unchanged. It did not test the complete
authored packet, preceding additions, plot acceptance or final terrain refresh.

Historical agreement failed: the run had 14 baseline Cinderwick buildings,
whereas the pinned #303 town has 13. The launch `PYTHONHASHSEED` was unset;
existing `geo5.routes`/`settle` also use `abs(hash(name))`, independently of the
seeded noise function. No recorded process hash seed or raw cache was found.
The pinned blockout retains 35 typed route records, but their exported
polylines are rounded and do not preserve the full raw ground/mask state.
Full baseline/route-table agreement was not established. The historical raw
classification of #334's cells is therefore **unrecoverable from the available
inputs**; the diagnostic is not a stock-producer or historical placement pass,
nor proof of a defect in #334. No fourth attempt, guessed seed, hard checker
rule or relocation follows from it.

The diagnostic script SHA-256 is
`1c27a25ba2235b899f44f58532d4eb107462d464fe5b79677da37529c050333f`.
Separate raw JSON, provenance and stdout logs are retained as
`forge-raw-oracle-instrumented*` outside the checkout. The provenance records
the unset hash seed and 3.2 GB RSS / 4 GB virtual / 4.2 GB shared-anonymous
memory guards. Python was 3.12.14, numpy 2.3.5 and scipy 1.17.0. Neither this
bounded result nor the fixture suite establishes full raw-world preservation.

## Verification and review evidence

Bounded local results so far:

- Eighteen adoption methods and all six unchanged Highgarth methods pass. Coverage
  includes exact input blobs, all 21 unchanged default record exports, exact
  Hearthold/Cape additions on the stated synthetic-level fixture terrain, retained
  original record fields, duplicates/unmatched IDs, metadata/count fabrication,
  actual door/street checks, tier/barrier/plot/window refusal controls, existing-use
  preservation and nested metadata validation. Source pins cover district/open-use
  descriptions as well as building records.
- The four new default/selection methods cover complete factory source-flow
  equivalence to #331, keyword-only defaults, no proposal lookup/adoption for an
  empty selection, actual entrypoint early refusal of unknown keys/wrong towns,
  and deliberate real `Town.adopt` dispatch with geometry/target refusal controls.
  Source-flow comparison and lightweight fixture execution do not claim full
  raw-map regeneration or numerical world equality.
- The Cinderwick three-cell fixture is a conservative `r`-as-`road` refusal
  control, not a proven raw-generator placement failure or placement approval.
- Python compilation and `git diff --check` pass.
- An independent source review identified missing existing-use, rear-plot-window,
  barrier-approach and nested metadata guards. Those guards and regressions were
  added before readiness; the original draft remains a partial checkpoint.
- The initial fixture tuple-index failure, subsequent geometry/count-cap and
  metadata assertions were retained as development failures, then corrected.
  Initial missing `skimage` was an environment import failure, not a source pass.
- Python 3.12 uses isolated scratch dependencies: scikit-image 0.26.0,
  networkx 3.7, imageio 2.38.1, tifffile 2026.10.15 and jsonschema 4.26.0.
  They are environment dependencies, not new project version policy.
- The first image-free numeric oracle stopped itself with exit 85 during
  `stage_old`, at its conservative 2.2 GB RSS ceiling. It produced no terrain
  result; cgroup OOM counters stayed zero. A separately logged retry also stopped
  in `stage_old` at its shared anonymous-memory guard (3.010 GB process peak RSS,
  4.243 GB shared anonymous memory), before producing cell or `Town.hand` results.
  It had a 3.2 GB RSS ceiling and 4 GB virtual allocation limit. Both logs are
  retained, no result JSON was produced, and neither attempt is credited as a pass.

Source-only Y12 packet: subject files are the two generator/exporter modules,
their dedicated test/document and the focused workflow; inputs are the exact table pins and the stored
blob pins. No generated town JSON, image, piece approval or Player source is
changed. Raster detail ratios, asset/scene screenshots and visual comparison are
not applicable evidence for these source-only changes. The full real-map
regeneration, final verify/art-reproduction exits and matching hosted CI are
**not yet established**. Keep the PR draft and labelled `needs-matt-review`.

The dedicated `town-generator-adoption.yml` workflow is authorised by scope
[6477336852](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6477336852).
It deliberately fetches exact #303/#331/#334–#336 commit objects, verifies
their blob pins through the suite, and runs all 18 adoption plus six unchanged
Highgarth methods. Existing generic Verify/Art/Screens and #331's workflow do
not invoke adoption methods. Draft jobs are skipped by the job-level draft
guard; a skipped or absent job is not a hosted pass. Its existing action pins and blockout dependency versions
come from #331, with jsonschema 4.26.0 from the isolated tested environment;
they define this test job's environment, not a new project version policy.
Hosted execution and full required gates on the final head remain pending.

Run the focused suite after fetching #303, the three proposal commits and #331:

```sh
python -m unittest scripts.review.test_town_generator_adoption scripts.review.test_highgarth_export -v
```

The lead has explicitly narrowed this PR to the partial interface. Readiness
still requires source review, full verify/art and matching hosted checks; Matt
must approve its inherited map/art dependency before any merge. The broader
historical adoption task remains blocked by reproducibility. Its future full
regeneration must go to scratch, compare every original record, routes,
terrain, life metadata, walls and pad against the pinned baseline, and establish
the exact adopted records before readiness. Existing named open uses and later
`geo55.write_plans` terrain refresh remain part of that acceptance. No device,
rendered gameplay, household authoring or whole-world acceptance is claimed.
