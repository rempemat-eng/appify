@tool
extends RefCounted
## One Python job (the ground bake) running beside the editor, not inside a frame of it: started as
## its own process, asked each frame whether it is still running, and stoppable. Its output goes to
## a log file, whose last line is the progress shown. No thread and no WorkerThreadPool task is
## used, so nothing is left unwaited when the editor closes.

## Runs a module as `python -m` would, from the repository root, with its output in a log file.
## argv: repository root, log file, module, then the module's own arguments.
const RUNNER := "import os,runpy,sys\nroot,log,module=sys.argv[1:4]\nstream=open(log,'w',buffering=1)\nsys.stdout=stream\nsys.stderr=stream\nos.chdir(root)\nsys.path.insert(0,root)\nsys.argv=[module]+sys.argv[4:]\nprint('started',module,flush=True)\ntry:\n    runpy.run_module(module,run_name='__main__')\nexcept SystemExit as stop:\n    code=stop.code\n    code=0 if code is None else code if isinstance(code,int) else 1\n    stream.flush()\n    os._exit(code)\n"

var pid := -1
var log_path := ""
var label := ""
var _started_msec := 0
var _exit_code := -1
var _cancelled := false

## Start `python -c <code> <arguments...>`; the code must write its output to `log`. False when the
## process could not be started.
func start(python: String, code: String, arguments: PackedStringArray, log: String, what: String = "") -> bool:
	log_path = log
	label = what
	_exit_code = -1
	_cancelled = false
	if FileAccess.file_exists(log):
		DirAccess.remove_absolute(log)
	var command := PackedStringArray(["-c", code])
	command.append_array(arguments)
	pid = OS.create_process(python, command)
	_started_msec = Time.get_ticks_msec()
	return pid > 0

## The bake of one zone, through RUNNER.
func start_module(python: String, repo: String, module: String, arguments: PackedStringArray, log: String, what: String = "") -> bool:
	var all := PackedStringArray([repo, log, module])
	all.append_array(arguments)
	return start(python, RUNNER, all, log, what)

func running() -> bool:
	if pid <= 0 or _exit_code != -1:
		return false
	if OS.is_process_running(pid):
		return true
	_exit_code = OS.get_process_exit_code(pid)
	return false

func seconds() -> float:
	return (Time.get_ticks_msec() - _started_msec) / 1000.0

## The exit code once the job has ended (-1 while it runs or when it never started).
func exit_code() -> int:
	running()
	return _exit_code

func cancelled() -> bool:
	return _cancelled

## The last line the job wrote, for the status line.
func last_line() -> String:
	var lines := output().strip_edges().split("\n")
	return lines[lines.size() - 1].strip_edges() if not lines.is_empty() else ""

func output() -> String:
	return FileAccess.get_file_as_string(log_path) if log_path != "" and FileAccess.file_exists(log_path) else ""

## Stop the job. Its outputs are whatever it had finished writing; the caller accepts none of them.
func cancel() -> void:
	if not running():
		return
	_cancelled = true
	OS.kill(pid)
	_exit_code = -2                    # killed: the engine forgets the process, so it is not asked after again

func progress_text() -> String:
	var line := last_line()
	return "%s: %d s%s" % [label if label != "" else "Working", int(seconds()), (" (" + line.left(80) + ")") if line != "" else ""]
