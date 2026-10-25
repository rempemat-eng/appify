# Independent handoff review

`core-inputs-qc.json` records the759-check audit of the35 core handoff files before this review directory was added. Its inventory is an explicit list of audited inputs, not a hash of its own report or of the later review tools.

The checker is read-only. To inspect the full current handoff, run from the handoff root:

```sh
python3 review/audit_package.py --package . --report /tmp/mygame-combat-handoff-qc.json
```

The output must be outside the inspected directory. Standard Python3 and Node.js24 suffice. This checks data/source integrity and contract structure, not formal JSON-schema validation, new art, Godot execution or plugin compatibility. The separate canonical validator executes the original pure-engine probes.
