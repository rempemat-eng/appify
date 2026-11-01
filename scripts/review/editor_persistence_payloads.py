"""Receiving script data and one bounded extension; loaded only after event-byte guards."""
import json
from pathlib import Path
import stat

PROBE = '''@tool
extends EditorPlugin
func _enter_tree() -> void:
    call_deferred("_paths")
func _paths() -> void:
    await get_tree().process_frame
    var paths = EditorInterface.get_editor_paths()
    var settings = EditorInterface.get_editor_settings()
    var out = {
        "version": Engine.get_version_info(), "executable": OS.get_executable_path(),
        "os_config": OS.get_config_dir(), "os_data": OS.get_data_dir(), "os_cache": OS.get_cache_dir(),
        "os_user": OS.get_user_data_dir(), "user_uri": ProjectSettings.globalize_path("user://"),
        "editor_config": paths.get_config_dir(), "editor_data": paths.get_data_dir(),
        "editor_cache": paths.get_cache_dir(),
        "project_settings": ProjectSettings.globalize_path(paths.get_project_settings_dir()),
        "settings_resource": settings.resource_path,
        "self_contained": paths.is_self_contained(), "portable_marker": paths.get_self_contained_file()
    }
    var file = FileAccess.open(OS.get_environment("EDITOR_PERSISTENCE_CANARY_OUTPUT"), FileAccess.WRITE)
    if file == null:
        push_error("EDITOR_PERSISTENCE canary output open failed")
        get_tree().quit(2)
        return
    file.store_string(JSON.stringify(out) + "\\n")
    file.close()
    print("EDITOR_PERSISTENCE_CANARY_PATHS=" + JSON.stringify(out))
    get_tree().quit(0)
'''

PYTHON_OBSERVER = "import json, os, sys, traceback, unittest\nfrom pathlib import Path\n\nselectors = json.loads(sys.argv[1])\noutput = Path(sys.argv[2])\nbase = Path(os.environ['PERSISTENCE_OUT'])\nstate = {'expected': selectors, 'observed': [], 'methods': {n: {'state': 'NOTRUN'} for n in selectors}}\nclass Result(unittest.TextTestResult):\n    def startTest(self, test):\n        self.current = test.id().removeprefix('scripts.art.kit.test_bake_publication.')\n        self.before = set(base.iterdir())\n        state['observed'].append(self.current)\n        state['methods'][self.current] = {'state': 'STARTED', 'id': test.id()}\n        output.write_text(json.dumps(state, indent=2) + '\\n')\n        super().startTest(test)\n    def addSuccess(self, test):\n        state['methods'][self.current]['state'] = 'PASS'\n        super().addSuccess(test)\n    def addFailure(self, test, err):\n        state['methods'][self.current].update(state='FAIL', exception_type=err[0].__name__,\n            message=str(err[1]), traceback=''.join(traceback.format_exception(*err)))\n        super().addFailure(test, err)\n    def addError(self, test, err):\n        state['methods'][self.current].update(state='ERROR', exception_type=err[0].__name__,\n            message=str(err[1]), traceback=''.join(traceback.format_exception(*err)))\n        super().addError(test, err)\n    def addSkip(self, test, reason):\n        state['methods'][self.current].update(state='SKIP', reason=reason)\n        super().addSkip(test, reason)\n    def addSubTest(self, test, subtest, err):\n        if err is not None:\n            state['methods'][self.current].update(state='ERROR', message='unexpected subtest',\n                traceback=''.join(traceback.format_exception(*err)))\n        super().addSubTest(test, subtest, err)\n    def stopTest(self, test):\n        state['methods'][self.current]['evidence_roots'] = [str(p) for p in sorted(set(base.iterdir()) - self.before)]\n        output.write_text(json.dumps(state, indent=2) + '\\n')\n        super().stopTest(test)\ntry:\n    suite = unittest.defaultTestLoader.loadTestsFromNames(\n        ['scripts.art.kit.test_bake_publication.' + n for n in selectors])\n    result = unittest.TextTestRunner(verbosity=2, failfast=True, resultclass=Result).run(suite)\n    state['success'] = result.wasSuccessful()\n    state['testsRun'] = result.testsRun\nexcept BaseException:\n    state['harness_error'] = traceback.format_exc()\n    raise\nfinally:\n    output.write_text(json.dumps(state, indent=2) + '\\n')\nsys.exit(0 if state.get('success') else 1)\n"

FRESH_LOAD_SCRIPT = "@tool\nextends EditorPlugin\nfunc _enter_tree() -> void:\n    var target := \"res://kit/terrain/materials.tres\"\n    var report := {\"cache_before\": ResourceLoader.has_cached(target), \"editor_hint\": Engine.is_editor_hint(), \"engine\": Engine.get_version_info(), \"load_calls\": 0}\n    print(\"EDITOR_FRESH_LOAD_BEFORE=\" + JSON.stringify(report))\n    if report.cache_before or not report.editor_hint or not EditorInterface.has_method(\"is_object_edited\"):\n        push_error(\"FRESH_LOAD prerequisites refused\")\n        get_tree().quit(2)\n        return\n    print(\"EDITOR_FRESH_LOAD_INTENT=\" + target)\n    var material: TileSet = ResourceLoader.load(target, \"TileSet\", ResourceLoader.CACHE_MODE_REUSE)\n    report.load_calls = 1\n    if material == null or material.get_source_count() != 1 or not material.has_source(0):\n        push_error(\"FRESH_LOAD exact TileSet source refused\")\n        get_tree().quit(2)\n        return\n    var atlas := material.get_source(0)\n    if not atlas is TileSetAtlasSource:\n        push_error(\"FRESH_LOAD atlas type refused\")\n        get_tree().quit(2)\n        return\n    report.root = {\"id\": material.get_instance_id(), \"type\": material.get_class(), \"path\": material.resource_path, \"edited\": EditorInterface.is_object_edited(material)}\n    report.atlas = {\"id\": atlas.get_instance_id(), \"type\": atlas.get_class(), \"path\": atlas.resource_path, \"edited\": EditorInterface.is_object_edited(atlas)}\n    report.cache_after = ResourceLoader.has_cached(target)\n    var file := FileAccess.open(OS.get_environment(\"EDITOR_FRESH_LOAD_OUTPUT\"), FileAccess.WRITE)\n    if file == null:\n        push_error(\"FRESH_LOAD output refused\")\n        get_tree().quit(2)\n        return\n    file.store_string(JSON.stringify(report) + \"\\n\")\n    file.close()\n    print(\"EDITOR_FRESH_LOAD_RESULT=\" + JSON.stringify(report))\n    call_deferred(\"_finish\")\nfunc _finish() -> void:\n    var filesystem := EditorInterface.get_resource_filesystem()\n    await get_tree().process_frame\n    while true:\n        while filesystem.is_scanning() or filesystem.is_importing():\n            await get_tree().process_frame\n        await get_tree().process_frame\n        if not filesystem.is_scanning() and not filesystem.is_importing():\n            break\n    print(\"EDITOR_FRESH_LOAD_SETTLED=\" + JSON.stringify({\"scanning\": filesystem.is_scanning(), \"importing\": filesystem.is_importing()}))\n    get_tree().quit(0)\n"

def fresh_load(c):
    project = c.root / "test-output" / "fresh-load"
    project.mkdir(mode=0o700)
    target = "game/kit/terrain/materials.tres"
    inputs = (target, "game/kit/terrain/palette.png", "game/kit/terrain/palette.png.import")
    copied = {}
    def guard_inputs():
        for name, before in copied.items():
            path = project / name.removeprefix("game/")
            info = path.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or stat.S_IMODE(info.st_mode) != 0o644
                    or info.st_size != before["bytes"] or c.payloads["sha256"](path) != before["sha256"]):
                raise RuntimeError("Fresh-load copied input changed: " + name)
    def copy_input(name):
        before = c.initial["game"][name]
        source = c.source / name
        info = source.lstat()
        if (before["mode"] != "100644" or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or info.st_size != before["bytes"] or c.payloads["sha256"](source) != before["sha256"]):
            raise RuntimeError("Fresh-load source input differs: " + name)
        destination = project / name.removeprefix("game/")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as src, destination.open("xb") as dst:
            dst.write(src.read(before["bytes"] + 1))
        destination.chmod(0o644)
        copied[name] = before
        guard_inputs()
        c.capacity()
    for name in inputs[1:]:
        copy_input(name)
    settings = project / "project.godot"
    base = 'config_version=5\n[application]\nconfig/name="MyGameFreshLoadProbe"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n'
    settings.write_text(base)
    absent = project / target.removeprefix("game/")
    if absent.exists() or absent.is_symlink():
        raise RuntimeError("Target must be absent during palette-only import")
    c.require_clean("load-palette-import", c.phase("load-palette-import", [
        str(c.engine), "--headless", "--audio-driver", "Dummy", "--path", str(project), "--import"], 30))
    guard_inputs()
    if absent.exists() or absent.is_symlink():
        raise RuntimeError("Palette preparation created target")
    copy_input(target)
    plugin = project / "addons/fresh_load"
    plugin.mkdir(parents=True)
    cfg = '[plugin]\nname="MyGameFreshLoad"\ndescription="Read-only resource load"\nauthor="MyGame"\nversion="1"\nscript="probe.gd"\n'
    (plugin / "plugin.cfg").write_text(cfg)
    (plugin / "probe.gd").write_text(FRESH_LOAD_SCRIPT)
    authored = {settings: base + '[editor_plugins]\nenabled=PackedStringArray("res://addons/fresh_load/plugin.cfg")\n',
                plugin / "plugin.cfg": cfg, plugin / "probe.gd": FRESH_LOAD_SCRIPT}
    settings.write_text(authored[settings])
    c.payloads["write_json"](c.evidence / "fresh-load-inputs-before.json", copied)
    report_path = c.evidence / "fresh-load-report.json"
    if report_path.exists() or report_path.is_symlink():
        raise RuntimeError("Fresh-load output is not fresh")
    c.env["EDITOR_FRESH_LOAD_OUTPUT"] = str(report_path)
    text = c.require_clean("fresh-load", c.phase("fresh-load", [
        str(c.engine), "--headless", "--audio-driver", "Dummy", "--verbose", "--editor",
        "--path", str(project)], 20))
    marker = "EDITOR_FRESH_LOAD_INTENT=res://kit/terrain/materials.tres"
    lines = text.splitlines()
    positions = [i for i, line in enumerate(lines) if line.strip() == marker]
    trace_lines = [(i, line.strip()) for i, line in enumerate(lines)
                   if line.strip().startswith("Loading resource:")
                   and "materials.tres" in line]
    exact_trace = "Loading resource: res://kit/terrain/materials.tres remapped: res://kit/terrain/materials.tres"
    if any(line != exact_trace for _, line in trace_lines):
        raise RuntimeError("Fresh-load target alias/remap refused")
    traces = [i for i, _ in trace_lines]
    if len(positions) != 1 or len(traces) != 1 or traces[0] <= positions[0]:
        raise RuntimeError("Fresh-load full-process target history refused")
    info = report_path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 1 <= info.st_size <= 8192:
        raise RuntimeError("Fresh-load report type/size refused")
    report = json.loads(report_path.read_text())
    if (report.get("cache_before") is not False or report.get("cache_after") is not True
            or report.get("editor_hint") is not True or report.get("load_calls") != 1
            or tuple(report.get("engine", {}).get(k) for k in ("major", "minor", "patch")) != (4, 7, 2)):
        raise RuntimeError("Fresh-load report prerequisites differ")
    ids = []
    for key, kind in (("root", "TileSet"), ("atlas", "TileSetAtlasSource")):
        row = report.get(key, {})
        path = row.get("path")
        if (type(row.get("id")) is not int or not -(1 << 63) <= row["id"] < (1 << 63)
                or row["id"] == 0 or row.get("type") != kind
                or type(row.get("edited")) is not bool or not isinstance(path, str)
                or (path != "res://kit/terrain/materials.tres" if key == "root"
                    else not path.startswith("res://kit/terrain/materials.tres::"))):
            raise RuntimeError("Fresh-load resource identity refused: " + key)
        ids.append(row["id"])
    if len(set(ids)) != 2:
        raise RuntimeError("Fresh-load resource identities collide")
    guard_inputs()
    for path, expected in authored.items():
        if path.is_symlink() or path.stat().st_nlink != 1 or path.read_text() != expected:
            raise RuntimeError("Fresh-load authored input changed")
    c.payloads["write_json"](c.evidence / "fresh-load-inputs-after.json", copied)
    c.guards["fresh_load_inputs"] = "PASS"
    c.output["fresh_load"] = {"report": report, "target_load_trace_lines": traces,
                             "intent_line": positions[0], "qualification":
                             "One fresh-process resource load only; not earliest H25 transition, SAVE or editor lifecycle acceptance."}
    c.output["state"] = "FRESH_LOAD_PENDING_TERMINAL_GUARDS"

