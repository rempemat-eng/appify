"""Hosted receiving adapter for reviewed R2 collector; no execution on prep refs.

Sole execution ref: codex/y47-focused-validation-run, created by lead only after
source review and explicit GO. The workflow/event commit is NOT the tested source:
all 21 tested input blobs below remain cab60780. No test body is modified.
R2 observer is byte-identical; execute/limits and WNOWAIT -> signal -> wait4
collection are reused. This source candidate has not been executed.
"""
import ast
import ctypes
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import subprocess
import sys
import time
import traceback

ROOT = Path(os.environ['RUNNER_TEMP']).resolve() / 'y47'
SOURCE = ROOT / 'source'
EVIDENCE = ROOT / 'evidence'
START = time.monotonic()
WALL = 180
COLLECT = 20
MIB = 1024 ** 2
SOURCE_HEAD = 'cab60780e977db491b7d4fc1d58bfc2870761697'
SOURCE_TREE = 'c3a0befba964a92d0eeb12a0cd6958394e8baa6f'
AUTHORITY_HEAD = '885b45ea4d6fd8cd2246d90903b8cebbba2705b4'
REQUIREMENTS_BLOB = '97a2d95b8b5d6c801ad0258cf44cbb6474a07a1e'
EXECUTION_REF = 'refs/heads/codex/y47-focused-validation-run'
RUNNER_PATHS = ('.github/workflows/y47-focused-validation.yml',
                'scripts/review/y47_validation_outer.py',
                'scripts/review/y47_validation_observer.py')
R2_ZIP_SHA256 = '4e353a92161229660efda598b0c99ee9b08dd0a02fdc1100508cf5e7a0334d12'
R2_OUTER_SHA256 = 'a62d2d974f4b112854489d359136f52536bb293f075e422c8e516493965b7184'
OBSERVER_SHA256 = '690c0c12ddc6ed04f9ca21c59e3b708e2749ec248531b823c0836a90f614889c'
DEPENDENCIES = {'Pillow': '12.3.0', 'numpy': '2.5.3', 'scipy': '1.18.1'}

MANIFEST = {'head': 'cab60780e977db491b7d4fc1d58bfc2870761697', 'tree': 'c3a0befba964a92d0eeb12a0cd6958394e8baa6f', 'route': 'exact remote UTF-8 Git blobs; no native checkout/index proof', 'files': [{'path': 'scripts/review/__init__.py', 'sha': 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391', 'mode': '100644', 'size': 0, 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, {'path': 'scripts/review/owned_launch.py', 'sha': '0e042782dff6b61afb5d615e5c1ca7ff552d84d2', 'mode': '100644', 'size': 8000, 'sha256': '5c5c1970662dd3ada77245e50059bbc52efc12e2983fa1cf20274b8c037bfd32'}, {'path': 'scripts/review/owned_broker.py', 'sha': '6c48d274403dea49ee6bf6286e07978473069317', 'mode': '100644', 'size': 25851, 'sha256': '1c991b899c00a609b25e5071e09b4587e0f741e4cb633bec0a4fb0f1f7681b70'}, {'path': 'scripts/review/test_owned_launch.py', 'sha': '099a1bc5e86cc5c93daaa2c4796222d1e70a917e', 'mode': '100644', 'size': 19428, 'sha256': 'c9cc264af40b803734af9b5d3a76f96786fc55d2e655f9bf7f0cf474b9803429'}, {'path': 'scripts/review/test_pr_sheet.py', 'sha': 'c04634f9d9ff361ac2ccb241e7d8a6f5cdef49e6', 'mode': '100644', 'size': 99768, 'sha256': '153ffb841a62d4f1eee5dcfe618932cee9f201fa7f9c4b3de5eb8f9c700ce724'}, {'path': 'scripts/review/pr_sheet.py', 'sha': 'd93f89ea9906e70537458c37bdccb44555001212', 'mode': '100644', 'size': 42852, 'sha256': 'a366837d67dbf0948ac859e5ac5407760be435344273fa45704b3ac75ae5c673'}, {'path': 'scripts/review/kit_representation.py', 'sha': 'f1b33f1a5b3e814d0cc466bc84490a9b66083614', 'mode': '100644', 'size': 6782, 'sha256': '1a5ab98dcb90ac867294cd15c904704e5cf7ba944bc0e4ec898ef82d8b1e2c1a'}, {'path': 'scripts/review/run.py', 'sha': '489e0ee98d00dbe0fb90c18cb5abd4ce7bd40efe', 'mode': '100644', 'size': 14057, 'sha256': '5ad4c5d4b2c8d4b39155cd15ac627e2dd3dbd50434993074252364152a1f4674'}, {'path': 'scripts/review/core.py', 'sha': '5a601696e3fea6d972eeecc94d0418d554b378a3', 'mode': '100644', 'size': 13236, 'sha256': '0d08adf998f9c949885a21a143e5d9fef1577ab601b235d62113d620a0395929'}, {'path': 'scripts/review/screen.py', 'sha': '3fe1189d3ab028855ad2771f8b4281c721e21911', 'mode': '100644', 'size': 25346, 'sha256': 'c5bbcf9e2eb7b23bf7b450c02039094f211e673a17eefb83d42803f2e324fb01'}, {'path': 'scripts/review/scene.py', 'sha': '0d7df7891f733585af5fa4cb1f3177dfb8a153ec', 'mode': '100644', 'size': 32500, 'sha256': 'a8fc8f43d7d77f39331fa6d7b01ece7dd8a3ddeb5cb1eb60667cf61aec89ef4d'}, {'path': 'scripts/review/bands.py', 'sha': 'c7a384a59953fd8e9844ac51824cdb0117500b56', 'mode': '100644', 'size': 8141, 'sha256': '97bdf84c58a044bb1e16c11558b54ff79fb292a253cc5e1e49ee874805902a8a'}, {'path': 'scripts/review/detail.py', 'sha': '8d30363b4cd502202e0aebfbf84222aa999fcb0d', 'mode': '100644', 'size': 11636, 'sha256': '41f225a09392378138c09056f1a8bcba7300cacb08c8c869e451f99e90a89668'}, {'path': 'scripts/review/construct.py', 'sha': 'f899558754d10d7687ffb9ea503a6be99d91b931', 'mode': '100644', 'size': 27792, 'sha256': 'fc00fa540a66e8521f76bc14a74e99e202c28bbd87c30e651b24b9ea624ba7ff'}, {'path': 'scripts/review/objects.py', 'sha': '575f007fb59981ab0d098f4b9063a915c3eec799', 'mode': '100644', 'size': 5014, 'sha256': '428c35fd279c2ca20a064348a0ea54183716909b033631e4048e0c8458b927e7'}, {'path': 'scripts/review/scale.py', 'sha': '0a6469939d4b24cb737fe0d0d0405b95b60ae6d1', 'mode': '100644', 'size': 36168, 'sha256': '4de6fc6326330fb892edf95fb3718a18cec6b0b9c276e36fde76f9375fcf9d7c'}, {'path': 'scripts/review/water.py', 'sha': 'af50a4ed029d5b95affd6d6f8e865b7b6a8c67e5', 'mode': '100644', 'size': 16226, 'sha256': '92453548903236152c76eca6b9e86573fa9dd7d55e4dcf33427703b9133ff6df'}, {'path': 'scripts/review/edges.py', 'sha': 'c76fb9fcc9232c3b86c1a2715827eed30f58feb6', 'mode': '100644', 'size': 8509, 'sha256': '17aea14bb590c6df6971b85a117499430c71535f8ecfb268f3c4be37094c5aa4'}, {'path': 'scripts/review/sizes.json', 'sha': '3007080aa43ae1c0f8abb914b363b9419c4e7b1b', 'mode': '100644', 'size': 28470, 'sha256': 'c3d9cf93019db9b5d1c8d3cb7863a0085b28b41c03c7dc714aa17997232cd592'}, {'path': 'scripts/review/eastward_bands.json', 'sha': 'e612e0b75936d2b610d6a89504e33676656d31ec', 'mode': '100644', 'size': 5438, 'sha256': '8360bdc6f0036f1067ae409d0779c0aa2ec649c0f7d6056552f6119db86d0cfa'}, {'path': 'scripts/art/size_guide.json', 'sha': 'f30ecb3249d771e5dc6cdf6546d50400b118cf57', 'mode': '100644', 'size': 45069, 'sha256': '7047de7c0d42043a43cbc8ca2f734b46b1a2212a7f9b2a11aa6ae6cd77a91af3'}], 'tree_lookup_response_sha': 'cab60780e977db491b7d4fc1d58bfc2870761697', 'parents': ['af9e6662411b9250455f5e1cba8a5550e1a2248e']}
METHODS = {'OwnedLaunchControls': ['test_nested_real_fake_producers_have_broker_parent_without_proc_reads',
                         'test_immediate_exit_and_nonzero_status_are_actual_wait_results',
                         'test_exec_failure_remains_nonzero_with_diagnostic',
                         'test_registration_refusal_never_runs_target_and_waits_for_closed_gate',
                         'test_cancel_while_gate_closed_refuses_target_exec',
                         'test_nested_cancellation_collects_all_registered_children',
                         'test_timeout_keeps_bounded_output_and_refuses_late_requests',
                         'test_duplicate_request_cannot_execute_target_twice',
                         'test_broken_client_channel_cancels_and_reaps_registered_job',
                         'test_missing_broker_credentials_and_connection_never_fall_back',
                         'test_stdout_stderr_text_and_checked_status_match_capture_contract',
                         'test_ignored_sigchld_refuses_before_any_service_spawn',
                         'test_unsupported_reaper_abi_refuses_before_spawn',
                         'test_inprocess_service_without_exclusive_authority_refuses',
                         'test_pending_parent_registration_refuses_before_any_actual_wait',
                         'test_lost_kernel_wait_never_becomes_synthetic_success',
                         'test_nocldwait_refuses_before_any_service_spawn',
                         'test_partial_frame_absolute_deadline_ignores_drip_progress',
                         'test_partial_frame_cancellation_collects_prelaunch_handler',
                         'test_repeated_cancel_preserves_control_reply_and_raw_collection',
                         'test_output_limit_fails_instead_of_returning_success',
                         'test_unregistered_native_descendant_is_explicitly_not_covered'],
 'OwnedAdapterControls': ['test_managed_git_keeps_binary_argv_environment_and_parent',
                          'test_managed_detector_exit_one_keeps_logs_hashes_and_wait_receipt',
                          'test_managed_python_runner_binds_subject_paths_not_subject_code',
                          'test_managed_timeout_remains_124_and_partial_logs_are_retained',
                          'test_managed_engine_error_at_zero_exit_is_still_rejected',
                          'test_managed_missing_inputs_and_stripped_credentials_never_launch_locally']}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    (EVIDENCE / name).write_text(json.dumps(value, indent=2) + '\n')

def guard(manifest):
    observed = []
    for row in manifest['files']:
        path = SOURCE / row['path']
        assert path.is_file() and not path.is_symlink(), row['path']
        assert sha(path) == row['sha256'], row['path']
        assert git_blob(path.read_bytes()) == row['sha'], row['path']
        assert path.stat().st_mode & 0o777 == int(row['mode'], 8) & 0o777, row['path']
        observed.append(dict(path=row['path'], sha256=sha(path)))
    return observed

def usage():
    return sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink())

def limits():
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (1024 ** 3, 1024 ** 3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * MIB, 16 * MIB))

def execute(label, selector, expected, environment):
    """Never reap the group leader before the last possible group signal."""
    log = EVIDENCE / (label + '.log')
    observations = EVIDENCE / (label + '-methods.json')
    command = [sys.executable, '-I', '-B', str(ROOT / 'run_selected.py'),
               str(SOURCE), selector, str(observations)]
    record = dict(selector=selector, command=command, expected_methods=expected,
                  status='STARTING', actual_wait=False)
    save(label + '-result.json', record)
    print(json.dumps(dict(phase=label, status='STARTING')), flush=True)
    process = None
    terminal = None
    resource_error = None
    signalled = False
    identity_lost = False
    with log.open('xb') as output:
        try:
            process = subprocess.Popen(command, cwd=SOURCE, env=environment, stdin=subprocess.DEVNULL,
                                       stdout=output, stderr=subprocess.STDOUT,
                                       start_new_session=True, preexec_fn=limits)
            while True:
                # WNOWAIT preserves the actual child identity/PID even after exit.
                try:
                    terminal = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                except ChildProcessError:
                    identity_lost, resource_error = True, 'WNOWAIT identity lost (ECHILD)'
                    break
                if terminal is not None:
                    break
                if time.monotonic() - START > WALL:
                    resource_error = 'overall 180s wall limit'
                    break
                if sum(p.stat().st_size for p in ROOT.rglob('*.log')) > 16 * MIB or usage() > 64 * MIB:
                    resource_error = 'owned output limit'
                    break
                time.sleep(.05)
        except BaseException as exc:
            resource_error = repr(exc)
        finally:
            if process is not None and not identity_lost:
                # This is our unreaped session leader. No kill/poll after wait4.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                    signalled = True
                except ProcessLookupError:
                    pass
                deadline = min(time.monotonic() + COLLECT, START + WALL + COLLECT)
                while True:
                    try:
                        pid, raw, ru = os.wait4(process.pid, os.WNOHANG)
                    except ChildProcessError:
                        identity_lost, resource_error = True, 'actual wait4 identity lost (ECHILD)'
                        break
                    if pid:
                        assert pid == process.pid
                        process.returncode = os.waitstatus_to_exitcode(raw)
                        record.update(returncode=process.returncode, raw_wait_status=raw, actual_wait=True,
                                      kernel_maxrss_bytes=ru.ru_maxrss * 1024,
                                      cpu_seconds=ru.ru_utime + ru.ru_stime)
                        break
                    if time.monotonic() > deadline:
                        resource_error = 'direct child collection exceeded bound'
                        break
                    time.sleep(.02)
                record.update(leader_was_observed_without_reap=terminal is not None,
                              group_signal_before_reap=signalled, resource_error=resource_error)
            record.update(identity_lost=identity_lost, resource_error=resource_error)
    observed = json.loads(observations.read_text()) if observations.is_file() else []
    actual_names = [name.rsplit('.', 1)[-1] for name, _state in observed]
    record.update(log_sha256=sha(log), observed=observed, log_bytes=log.stat().st_size)
    record['not_run_methods'] = sorted(set(expected) - set(actual_names))
    if sum(p.stat().st_size for p in ROOT.rglob('*.log')) > 16 * MIB or usage() > 64 * MIB:
        resource_error = 'owned output/log limit after child collection'
        record['resource_error'] = resource_error
    record['status'] = ('PASSED' if record.get('returncode') == 0 and not resource_error
                        and sorted(actual_names) == sorted(expected)
                        and all(state == 'ok' for _name, state in observed) else 'FAILED')
    save(label + '-result.json', record)
    print(json.dumps(dict(phase=label, status=record['status'], observed=len(observed))), flush=True)
    return record



def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def git(checkout, *args):
    completed = subprocess.run(['git', '-C', str(checkout), *args],
                               stdin=subprocess.DEVNULL, capture_output=True,
                               timeout=10, check=True)
    return completed.stdout


def selected_methods():
    """AST inventory only, before any project import or service startup."""
    observed = {}
    for filename, name in [('test_owned_launch.py', 'OwnedLaunchControls'),
                           ('test_pr_sheet.py', 'OwnedAdapterControls')]:
        tree = ast.parse((SOURCE / 'scripts/review' / filename).read_bytes())
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name]
        assert len(classes) == 1, name
        observed[name] = sorted(node.name for node in classes[0].body
                                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'))
        assert observed[name] == sorted(METHODS[name]), name
    return observed


def socket_proof():
    # All literal selected-class TMP prefixes crossed with every Broker root
    # literal, as in R2. Include the permanent canary root separately. No sockets
    # are created by this proof; use os.fsencode for the actual receiving path.
    prefixes = set()
    for filename, name in [('test_owned_launch.py', 'OwnedLaunchControls'),
                           ('test_pr_sheet.py', 'OwnedAdapterControls')]:
        tree = ast.parse((SOURCE / 'scripts/review' / filename).read_bytes())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
        for node in ast.walk(cls):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == 'prefix' and isinstance(kw.value, ast.Constant):
                        prefixes.add(kw.value.value)
    assert prefixes == {'owned-control-', 'owned-git-', 'owned-command-',
                        'owned-tool-routing-', 'owned-timeout-', 'owned-engine-log-', 'owned-refusal-'}
    folders = ['broker', 'fixture-broker', 'ignored', 'unsupported', 'no-authority',
               'unstarted-service', 'auto-reap', 'partial-frame-broker']
    paths = [ROOT / 't' / (prefix + '12345678') / folder / 'launch.sock'
             for prefix in sorted(prefixes) for folder in folders]
    paths.append(EVIDENCE / 'service-canary' / 'launch.sock')
    rows = [dict(path=str(path), bytes=len(os.fsencode(path))) for path in paths]
    proof = dict(kind='R2 conservative cross-product, actual hosted receiving roots',
                 suffix_bytes=8, limit_bytes=107, paths=rows,
                 max_bytes=max(row['bytes'] for row in rows))
    (ROOT / 'socket-path-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    assert proof['max_bytes'] <= 107, proof
    return proof


def prepare_hosted():
    """Bind reviewed runner/event, exact tested checkout, versions and paths."""
    assert os.environ.get('GITHUB_EVENT_NAME') == 'push'
    assert os.environ.get('GITHUB_REPOSITORY') == 'rempemat-eng/appify'
    assert os.environ.get('GITHUB_REF') == EXECUTION_REF
    assert os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'no automatic rerun allocation'
    runner = Path(os.environ['GITHUB_WORKSPACE']) / 'runner'
    checkout = Path(os.environ['GITHUB_WORKSPACE']) / 'subject'
    authority = Path(os.environ['GITHUB_WORKSPACE']) / 'authority'
    workflow_commit = os.environ['GITHUB_SHA']
    assert git(runner, 'rev-parse', 'HEAD').decode().strip() == workflow_commit
    parents = git(runner, 'show', '-s', '--format=%P', workflow_commit).decode().split()
    assert len(parents) == 1, parents
    git(runner, 'merge-base', '--is-ancestor', SOURCE_HEAD, workflow_commit)
    changed = git(runner, 'diff', '--name-only', SOURCE_HEAD, workflow_commit).decode().splitlines()
    assert sorted(changed) == sorted(RUNNER_PATHS), changed
    assert git(checkout, 'rev-parse', 'HEAD').decode().strip() == SOURCE_HEAD
    assert git(checkout, 'rev-parse', 'HEAD^{tree}').decode().strip() == SOURCE_TREE
    assert git(authority, 'rev-parse', 'HEAD').decode().strip() == AUTHORITY_HEAD
    runner_rows = []
    for name in RUNNER_PATHS:
        path = runner / name
        data = path.read_bytes()
        committed = git(runner, 'show', workflow_commit + ':' + name)
        assert data == committed and not path.is_symlink(), name
        runner_rows.append(dict(path=name, sha=git_blob(data), sha256=sha(path),
                                mode=oct(path.stat().st_mode & 0o777)))
    assert Path(__file__).resolve() == runner / RUNNER_PATHS[1]
    assert sha(runner / RUNNER_PATHS[2]) == OBSERVER_SHA256
    requirements = authority / '.github/workflows/verify.yml'
    assert not requirements.is_symlink() and git_blob(requirements.read_bytes()) == REQUIREMENTS_BLOB
    for name, version in DEPENDENCIES.items():
        assert name + '==' + version in requirements.read_text(), name
    save('runner-provenance.json', dict(workflow_commit=workflow_commit,
         workflow_tree=git(runner, 'rev-parse', 'HEAD^{tree}').decode().strip(),
         ordered_parents=parents, files=runner_rows,
         tested_source_head=SOURCE_HEAD, tested_source_tree=SOURCE_TREE,
         prior_r2_zip_sha256=R2_ZIP_SHA256, prior_outer_sha256=R2_OUTER_SHA256,
         observer_byte_identical_sha256=OBSERVER_SHA256,
         execution_authority='lead-controlled execution ref after separate review and explicit GO'))
    # Portable inputs, not the receiving Git administrative directory or venv.
    SOURCE.mkdir(exist_ok=False)
    assert len(MANIFEST['files']) == 21
    for row in MANIFEST['files']:
        source = checkout / row['path']
        assert not source.is_symlink() and source.is_file(), row['path']
        data = source.read_bytes()
        assert len(data) == row['size'] and git_blob(data) == row['sha'], row['path']
        assert sha(source) == row['sha256'], row['path']
        assert source.stat().st_mode & 0o777 == int(row['mode'], 8) & 0o777, row['path']
        target = SOURCE / row['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(int(row['mode'], 8) & 0o777)
    (ROOT / 'provenance.json').write_text(json.dumps(MANIFEST, indent=2) + '\n')
    shutil.copyfile(runner / RUNNER_PATHS[1], ROOT / 'outer.py')
    shutil.copyfile(runner / RUNNER_PATHS[2], ROOT / 'run_selected.py')
    shutil.copyfile(runner / RUNNER_PATHS[0], ROOT / 'y47-focused-validation.yml')
    shutil.copyfile(requirements, ROOT / 'main885b-verify.yml')
    versions = dict(python=sys.version, executable=sys.executable,
                    implementation=platform.python_implementation(),
                    system=platform.system(), machine=platform.machine(),
                    libc=platform.libc_ver(), dependencies={
                        name: importlib.metadata.version(name) for name in DEPENDENCIES},
                    APIs={name: hasattr(os, name) for name in
                          ['pidfd_open', 'wait4', 'waitid', 'WNOWAIT', 'sched_setaffinity', 'sched_getaffinity']},
                    pidfd_signal=hasattr(signal, 'pidfd_send_signal'))
    save('versions.json', versions)
    assert versions['implementation'] == 'CPython' and sys.version_info[:2] == (3, 12)
    assert versions['system'] == 'Linux' and versions['machine'] == 'x86_64'
    assert versions['libc'][0] == 'glibc' and all(versions['APIs'].values()) and versions['pidfd_signal']
    assert versions['dependencies'] == DEPENDENCIES
    # A pidfd for this live outer verifies the host syscall without any service
    # startup/retry or PID-reuse experiment. Actual child wait4/WNOWAIT follow in
    # the single persistent-log service canary and unchanged controls.
    descriptor = os.pidfd_open(os.getpid())
    try:
        signal.pidfd_send_signal(descriptor, 0)
    finally:
        os.close(descriptor)
    save('method-inventory.json', selected_methods())
    proof = socket_proof()
    plan = dict(head=SOURCE_HEAD, tree=SOURCE_TREE, workflow_commit=workflow_commit,
                methods=METHODS, sequence=['service_canary', 'OwnedLaunchControls', 'OwnedAdapterControls'],
                limits=dict(cpu=1, wall_seconds=WALL, collection_seconds=COLLECT,
                            hard_as_per_process=1024 ** 3, owned_bytes=64 * MIB, combined_log_bytes=16 * MIB),
                outer_sha256=sha(Path(__file__)), observer_sha256=OBSERVER_SHA256,
                manifest_sha256=sha(ROOT / 'provenance.json'),
                socket_proof_sha256=sha(ROOT / 'socket-path-proof.json'),
                max_socket_bytes=proof['max_bytes'],
                requirements_head=AUTHORITY_HEAD, requirements_blob=REQUIREMENTS_BLOB,
                dependency_versions=DEPENDENCIES,
                prior_r2_zip_sha256=R2_ZIP_SHA256,
                command=[sys.executable, '-I', '-B', str(Path(__file__).resolve())],
                coverage='single canary then unchanged22+6; no old95 suite/engine/Node/full gates/Y12/acceptance')
    (ROOT / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    protected = {name: sha(ROOT / name) for name in
                 ['outer.py', 'run_selected.py', 'plan.json', 'provenance.json',
                  'socket-path-proof.json', 'y47-focused-validation.yml', 'main885b-verify.yml']}
    protected.update({str(runner / row['path']): row['sha256'] for row in runner_rows})
    save('command.json', dict(argv=sys.argv, executable=sys.executable, cwd=str(Path.cwd()),
                              plan=plan, runner_guards=protected,
                              run_id=os.environ['GITHUB_RUN_ID'], attempt=os.environ['GITHUB_RUN_ATTEMPT']))
    return plan, protected


def initial_result():
    return dict(head=SOURCE_HEAD, tree=SOURCE_TREE,
                workflow_commit=os.environ.get('GITHUB_SHA'), status='FAILED',
                runs=[], orphan_waits=[], all_owned_children_reaped=False,
                controls={name + '.' + method: 'NOTRUN' for name, methods in METHODS.items() for method in methods})


def main():
    plan, protected = prepare_hosted()
    go = dict(authorization='lead-controlled execution-ref push', head=SOURCE_HEAD,
              workflow_commit=os.environ['GITHUB_SHA'], outer_sha256=plan['outer_sha256'])
    run_marker = EVIDENCE / 'invocation.json'
    with run_marker.open('x') as stream:
        json.dump(dict(go=go, started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())), stream)
    manifest = json.loads((ROOT / 'provenance.json').read_text())
    before = guard(manifest)
    save('source-before.json', before)
    limits()
    # Dedicated outer is the sole waiter. Adopt/reap any orphaned test descendants.
    libc = ctypes.CDLL(None, use_errno=True)
    assert libc.prctl(36, 1, 0, 0, 0) == 0, 'subreaper unavailable'
    assert signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    runtime = ROOT / 't'
    runtime.mkdir(exist_ok=False)
    (runtime / 'xdg-runtime').mkdir(mode=0o700)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1',
               OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1',
               TMPDIR=str(runtime), XDG_CONFIG_HOME=str(runtime / 'config'),
               XDG_DATA_HOME=str(runtime / 'data'), XDG_CACHE_HOME=str(runtime / 'cache'),
               XDG_RUNTIME_DIR=str(runtime / 'xdg-runtime'))
    for key in ('GODOT', 'DISPLAY', 'XAUTHORITY', 'MYGAME_OWNED_SOCKET',
                'MYGAME_OWNED_TOKEN', 'MYGAME_OWNED_PARENT'):
        env.pop(key, None)
    result = initial_result()
    try:
        for label, selector in [('canary', 'service_canary'),
                                ('broker22', 'scripts.review.test_owned_launch.OwnedLaunchControls'),
                                ('adapter6', 'scripts.review.test_pr_sheet.OwnedAdapterControls')]:
            if time.monotonic() - START >= WALL:
                result['runs'].append(dict(selector=selector, status='NOTRUN',
                                           reason='overall wall budget exhausted before launch'))
                break
            expected = ['service_canary'] if label == 'canary' else plan['methods'][selector.rsplit('.', 1)[1]]
            row = execute(label, selector, expected, env)
            result['runs'].append(row)
            if row['status'] != 'PASSED':
                break
        result['status'] = 'PASSED' if len(result['runs']) == 3 and all(r['status'] == 'PASSED' for r in result['runs']) else 'FAILED'
    except BaseException as exc:
        result['exception'] = repr(exc)
        result['status'] = 'FAILED'
    finally:
        deadline = min(time.monotonic() + COLLECT, START + WALL + COLLECT)
        while True:
            try:
                pid, raw, ru = os.wait4(-1, os.WNOHANG)
            except ChildProcessError:
                result['all_owned_children_reaped'] = True
                break
            if pid:
                result['status'] = 'FAILED'
                result['orphan_waits'].append(dict(pid=pid, raw_wait_status=raw,
                                                   kernel_maxrss_bytes=ru.ru_maxrss * 1024))
            elif time.monotonic() > deadline:
                result['all_owned_children_reaped'] = False
                result['status'] = 'FAILED'
                break
            else:
                time.sleep(.02)
        try:
            after = guard(manifest)
        except (OSError, AssertionError) as exc:
            after = []
            result['source_guard_error'] = repr(exc)
            result['status'] = 'FAILED'
        save('source-after.json', after)
        result['runner_guards'] = {name: sha(ROOT / name) == expected for name, expected in protected.items()}
        result.update(source_unchanged=before == after, owned_bytes=usage(),
                      elapsed_seconds=round(time.monotonic() - START, 4),
                      limits=dict(wall_seconds=WALL, collection_seconds=COLLECT, hard_as_per_process=1024 ** 3),
                      coverage='Service canary then exact 22+6 controls only; no old95 suite/engine/display/full gates/Y12/art acceptance')
        if before != after or result['owned_bytes'] > 64 * MIB or not all(result['runner_guards'].values()):
            result['status'] = 'FAILED'
        # Failfast leaves later phases and controls explicitly NOTRUN.
        for label, selector in [('canary', 'service_canary'),
                                ('broker22', 'scripts.review.test_owned_launch.OwnedLaunchControls'),
                                ('adapter6', 'scripts.review.test_pr_sheet.OwnedAdapterControls')]:
            if not any(row['selector'] == selector for row in result['runs']):
                result['runs'].append(dict(selector=selector, status='NOTRUN',
                                           reason='earlier phase/precondition failed or budget exhausted'))
        for row in result['runs']:
            for name, state in row.get('observed', []):
                key = '.'.join(name.split('.')[-2:])
                if key in result['controls']:
                    result['controls'][key] = state
        save('result.json', result)
    print(json.dumps(dict(status=result['status'], runs=[r['status'] for r in result['runs']],
                          all_owned_children_reaped=result['all_owned_children_reaped'])))
    return 0 if result['status'] == 'PASSED' else 1

if __name__ == '__main__':
    ROOT.mkdir(mode=0o700, exist_ok=True)
    EVIDENCE.mkdir(exist_ok=True)
    marker = ROOT / 'hosted-once.json'
    try:
        with marker.open('x') as stream:
            json.dump(dict(workflow_commit=os.environ.get('GITHUB_SHA'),
                           started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())), stream)
        save('result.json', initial_result())
        code = main()
    except BaseException:
        error = traceback.format_exc()
        (EVIDENCE / 'outer-first-error.txt').write_text(error)
        traceback.print_exc()
        result = json.loads((EVIDENCE / 'result.json').read_text()) if (EVIDENCE / 'result.json').exists() else initial_result()
        result.update(status='FAILED', setup_or_collection_error=error)
        save('result.json', result)
        code = 1
    raise SystemExit(code)
