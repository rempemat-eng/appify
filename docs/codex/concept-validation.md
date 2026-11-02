# Concept validation: W0 and W1 together

Task `W0-semantic/r1`, slot `flint`, claim [6476097421](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6476097421).

The reported 30 deferred-runtime errors are already resolved by W1. Combining the unchanged W0 corpus with W1's existing validator accepts all 129 concepts without allocating material IDs, painters or asset paths. This follow-up preserves that implementation and fixes a separate malformed-input crash in the same validator.

## Pinned inputs

| Source          | Exact input                                                                                                                                                                                                                                                                             | What it establishes                                                                                                                                                      |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Original editor | [`9bfc49da`, `schema.py`](https://github.com/rempemat-eng/appify/blob/9bfc49da6c4f593b515fbd242d38e9cfca129b5b/scripts/art/kit/schema.py)                                                                                                                                               | The old semantic validator requires runtime blocks regardless of approval state.                                                                                         |
| W0 #306         | [`7e816ab0`, catalogue](https://github.com/rempemat-eng/appify/blob/7e816ab09107424af3fc7b1d01689955de8b57c6/docs/vision/kit-catalogue.md) and [`game/data/kit/concepts/`](https://github.com/rempemat-eng/appify/tree/7e816ab09107424af3fc7b1d01689955de8b57c6/game/data/kit/concepts) | 129 unapproved review records, including 22 terrain and eight transition concepts. The catalogue describes the old validator's deliberate 30 failures.                   |
| W1 #307         | [`fd667dd1`, `schema.py`](https://github.com/rempemat-eng/appify/blob/fd667dd1d5e778b03d96bcadd51a2fdb15372953/scripts/art/kit/schema.py) and [`test_kit.py`](https://github.com/rempemat-eng/appify/blob/fd667dd1d5e778b03d96bcadd51a2fdb15372953/scripts/art/kit/test_kit.py)         | Concepts may defer runtime blocks; supplied blocks still undergo structural validation. Concepts are refused under the live-piece directory, including during migration. |
| Editor #302     | [`04228475`, world-editor.md](https://github.com/rempemat-eng/appify/blob/04228475cbd9fb76e0a0a9af52240d7e40a5d858/docs/world-editor.md)                                                                                                                                                | The library gate and Matt's approval precede production use.                                                                                                             |

The new branch starts at W1's real head and merges W0 as an unchanged dependency, with explicit lead authorisation. No original W0, W1 or editor branch is rewritten. W0's catalogue and every concept record remain unchanged; its historical failure description must be read against the source revision it names.

## Reproduced diagnosis

Using the original `9bfc49da` semantic function on the actual W0 records, with the concept-enabled structural schema:

- All 129 records pass structural validation.
- Exactly 30 have semantic errors: 22 missing terrain blocks and eight missing transition blocks.
- W1's unchanged semantic function accepts all 129.
- The combined branch's existing live library contains 106 pieces, and all 106 validate. The catalogue's 98-piece figure belongs to its earlier editor source, not this later library.

Review-only `rendering.contact_ao` and `rendering.cast_shadow` descriptors already exist in W0. Their presence is not an allocated PNG, painter or terrain material. The initial regression draft incorrectly forbade the whole optional rendering block; that test assumption was corrected after inspecting the real records. No concept data was removed to make the test pass.

## The actual code correction

The existing checker crashes before reporting structural errors for a JSON array, null or boolean at the root, an array/null approval block, or an array ID. The new shape guards let the structural validator report these invalid inputs. Semantic and file-identity checks no longer assume a valid dictionary or hashable ID before that assumption is established.

This does not change the concept-stage exception, required runtime blocks for later stages, the approved-piece reviewer/date rule, JSON Schema, migrations, material identities, artwork or placement behaviour. An invalid approval shape does not acquire the concept exception.

## Regression coverage

`scripts/art/kit/test_concept_schema.py` exercises the actual corpus, not a duplicate set of concept records:

- All 129 records and the real CLI pass, while their approval states remain `concept`.
- An independent Draft 2020-12 validator checks all 129 actual records and malformed controls. This optional test explicitly skips when `jsonschema` is absent; a skip is not independent structural proof.
- Each of the 30 deferred records still needs its runtime block when changed in memory to candidate, gated, approved, rejected or retired.
- Current-schema migration leaves all concept bytes and mtimes unchanged.
- Malformed records are diagnosed through the checker and CLI, and refused by migration.
- Malformed supplied terrain/transition blocks remain invalid.
- All 106 current live pieces and the existing invalid controls retain their validation outcomes.
- Default build-library intake excludes every concept ID.
- Even a concept with complete copied runtime metadata is refused in the live-piece directory; migration does not alter that input.

Run the focused suite explicitly:

```sh
python3 -m unittest scripts.art.kit.test_concept_schema -v
python3 -m unittest scripts.art.kit.test_kit
python3 -m scripts.art.kit.schema
python3 -m scripts.art.kit.schema game/data/kit/concepts/*.json
npm run verify
npm run check:art-repro
```

The existing package command names `test_kit` explicitly; it does not auto-discover the new module. Under the lead's narrow scope extension, `.github/workflows/kit-concept-validation.yml` runs the new module and both existing independent parity tests with pinned Python dependencies. It triggers on kit code, library/schema, concept corpus and workflow changes, and waits while a PR is draft. No shared package/check-list change is needed. A general workflow result alone still does not establish that this focused job executed.

Independent structural validation was also run with Python 3.12.14 and `jsonschema` 4.26.0 in an isolated scratch installation. All 129 actual records passed Draft 2020-12 validation, malformed controls were rejected, and the two previously skipped existing schema/source-binding parity tests passed. The isolated dependency versions were `jsonschema-specifications` 2025.9.1, `referencing` 0.37.0, `rpds-py` 2026.9.1, `attrs` 26.1.0 and `typing-extensions` 4.16.0. No shared runtime, repository dependency or lockfile was changed.

## Review boundary

There are no authored raster, painter, material-ID, schema-JSON, concept-data, town, actor or game-rule changes. Raster asset/scene comparisons and placement approval are not supplied by these schema tests. The inherited editor foundation remains unapproved and cannot be carried into main without Matt's acceptance. The PR carries `needs-matt-review` under the current kit-review policy; the lead owns integration.

Default library isolation and schema/migration refusal are covered here. This is not a claim that every direct low-level builder call independently enforces approval, nor a substitute for W3's placement refusals and combined-editor testing.
