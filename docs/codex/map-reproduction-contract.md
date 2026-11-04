# Prospective map seed contract

MyGame · slot=basalt · Y24/r1 · [ASSIGN6483617223](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483617223) · [ACK6483637519](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483637519).

This is a prospective seed correction on unchanged #343's real head `aa1161cdb03a3dc98d7d38bb41205edbe757b52b`. It removes process-random Python name hashes from three producer bindings. It does not establish complete map reproducibility or equality to historical #303. No raw map has been generated for this step.

## Source and the reproduced defect

| Source at #343                             | Blob                                       | Relevant behavior                                                                                                                      |
| ------------------------------------------ | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/vision/research/blockout/geo5.py`    | `7fc21a99a481d37df93bb9877e95cbcb77bb671c` | `routes` used `abs(hash(name)) % 1000`; `settle` used `% 997` for noise.                                                               |
| `docs/vision/research/blockout/towns55.py` | `ee3906f3e485a4fc55650f81de9a368452f30826` | `Town` used `seed or abs(hash(name)) % 2**31`.                                                                                         |
| `docs/vision/research/blockout/geo55.py`   | `20013f98a13b939bdc2ae3789ec92f4b5030db53` | `add_route` already uses unsigned UTF-8 CRC32 names, and the documented producer command uses `python3 -I`. This file stays unchanged. |

Python's isolated `-I` launch ignores `PYTHONHASHSEED`. Two isolated interpreters, both supplied `PYTHONHASHSEED=0`, reported `sys.flags.ignore_environment=1` and different hashes for the same name. An environment-only launcher would not correct this source defect.

Before the producer edits, the new real-consumer cross-process test failed: route points/seeds, settlement seed and town streams differed between processes. The initial five-method red run also reported the absent new helper; those API errors are development evidence, not 31 separate map defects. Its exact log and source guards are retained in the PR evidence.

## Seed policy and compatibility

The tiny shared `geo5.stable_name_seed(name, modulus)` returns `zlib.crc32(name.encode('utf-8')) % modulus`, extending the existing `geo55.add_route` convention. The real route, settlement and fallback-town bindings retain their respective `1000`, `997` and `2**31` moduli. No new RNG algorithm or seed registry is introduced.

`Town` now distinguishes absent/`None` from an explicit numerical seed. Omitted or `None` uses the stable name helper; an explicit seed goes unchanged to `numpy.random.default_rng`, including literal zero. The lead authorised the necessary default-sentinel change from `seed=0` to `seed=None` within the same constructor. Previously explicit zero selected the name fallback, so honoring literal zero is a clarified **prospective** API behavior, not a claim of old byte compatibility. Keyword and positional numerical seeds are covered.

A source audit of all 22 production `Town` call sites in `geo55.py` and `towns55.py` found explicit nonzero keyword seed expressions at each site, including the `300+i`, `400+i` and `500+i` loops. No current production caller omits the seed, passes `None` or zero, or supplies it positionally. The signature order and all other constructor behavior remain unchanged. These observations describe the pinned source, not all possible external callers.

## Bounded executable evidence

The new module `scripts.review.test_map_seed_reproducibility` executes the actual imported helper, `geo5.routes`, `geo5.settle` and `Town` constructor:

- Known CRC32/UTF-8 names exercise the unchanged caller moduli.
- Route and settlement spies verify the actual call sites use the shared helper. Real route meander arithmetic and town RNG streams execute in the fixture.
- Explicit numerical seeds, including zero, retain the corresponding NumPy streams and bypass fallback, through keyword and positional calls.
- Five fresh subprocess configurations compare the actual consumer outputs: normal launches with hash seeds `0`/`91`, isolated launches with both values and an unset value. The tests confirm the actual isolation flag.

The test context is 12×12 cells. Large-canvas line rasterisation, settlement-noise arithmetic and city painting are bounded fixture substitutes; these controls prove seed binding and process independence, not continent geometry. The isolated probe explicitly receives its parent's already-installed scientific dependency locations, which supports the local scratch dependency target without pretending `PYTHONPATH` survives `-I`.

Run the focused source/fixture checks:

```sh
python3 -m unittest scripts.review.test_map_seed_reproducibility -v
python3 -m unittest scripts.review.test_town_generator_adoption scripts.review.test_highgarth_export -v
```

The new dedicated workflow persists the five seed methods with the existing pinned actions and blockout dependency versions. The unchanged adoption workflow already triggers on both producer files and retains its 24 adoption/Highgarth methods. No shared package/check-list changes are needed. Draft-skipped or path-filtered jobs are not passes.

The initial combined focused run passed 29 methods with zero skips and unchanged source guards. Final exact-source results and log hashes belong in the PR/checkpoint. Full final `npm run verify`, zero lint, ordinary art reproduction and actual matching hosted coverage remain pending under the lead's serial allocation; this source step stays draft.

## Historical and review boundaries

Historical #303 did not preserve its interpreter hash seed or full raw terrain. The earlier instrumented run's Cinderwick baseline count differed from the committed town; the questioned route cells remain historically unclassified. This seed policy neither recovers that state nor proves that a proposed cottage is wrongly placed. No additional historical raw diagnostic, guessed seed, relocation or terrain/checker exception follows.

The #343 authoring interface remains off by default. No proposal packets, committed generated town JSON/PNG/bakes or route geometry, pad clearance, approvals, Player source or game rules change here. A later forward map candidate needs a separate allocation, complete source/dependency/seed provenance, actual typed terrain and mask evidence, source-preservation checks and applicable art/map review. Numerical seed stability alone is insufficient.

For the later review packet, the committed source reports canvas area growth of 15.49% and usable-land growth of 26.1%; these are different metrics. Highgarth's later written 24–36 guide and Neon's provisional 72-counted/81-record plan remain visible source facts rather than newly approved quotas. This task changes none of them.

The inherited #343/#331/#303 foundations remain unapproved. The lead reviews and integrates; Matt's explicit OK on the applicable PR is still required for art/map merging.
