"""Y47 focused controls, AUTHORED BUT UNRUN under source-only GO6503275523.

Future allocation must execute every method with real Linux pidfds, tiny private
fake producers only, and retain errors/capability refusals rather than skips.
No engine, display, project assets or /proc namespace setup is used here.
"""
from __future__ import annotations

import builtins
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from . import owned_launch as client
from .owned_broker import Broker


class OwnedLaunchControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='owned-control-')
        self.root = Path(self.temporary.name)
        self.broker = Broker(self.root / 'broker').__enter__()
        self.env = self.broker.environment()
        self.env['PYTHONPATH'] = str(Path(__file__).resolve().parents[2])
        self.env['GODOT'] = str(self.root / 'fake-engine.py')
        self.env['DISPLAY'] = ':SOURCE_CONTROL_ONLY'

    def tearDown(self):
        try:
            self.broker.__exit__(None, None, None)
        finally:
            self.temporary.cleanup()

    def run_fake(self, code, **kwargs):
        return client.run([sys.executable, '-c', code], env=self.env, cwd=self.root,
                          timeout=kwargs.pop('timeout', 4), **kwargs)

    def wait_file(self, path, seconds=3):
        deadline = time.monotonic() + seconds
        while not path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(path.exists(), 'bounded fake producer did not reach its marker')

    def test_nested_real_fake_producers_have_broker_parent_without_proc_reads(self):
        engine = self.root / 'fake-engine.py'
        engine.write_text("import os,json,sys\nprint(json.dumps({'parent':os.getppid(),'arg':sys.argv[1],"
                          "'value':os.environ['OWNED_CONTROL_VALUE']}))\nprint('engine stderr',file=sys.stderr)\n")
        scene = self.root / 'fake-scene.py'
        scene.write_text("import os,sys,json\nfrom scripts.review import owned_launch as c\n"
                         f"r=c.run([sys.executable,{str(engine)!r},'space and unicode λ'],env=os.environ,timeout=3)\n"
                         "print(json.dumps({'parent':os.getppid(),'engine':json.loads(r.stdout),"
                         "'receipt':r.owned_receipt}))\nsys.stderr.buffer.write(r.stderr)\n")
        producer = ("import os,sys,json\nfrom scripts.review import owned_launch as c\n"
                    f"r=c.run([sys.executable,{str(scene)!r}],env=os.environ,timeout=4)\n"
                    "print(json.dumps({'parent':os.getppid(),'scene':json.loads(r.stdout)}))\n"
                    "sys.stderr.buffer.write(r.stderr)\n")
        original_open, original_listdir = builtins.open, os.listdir

        def unavailable_proc(path, *args, **kwargs):
            if isinstance(path, (str, os.PathLike)) and str(path).startswith('/proc'):
                raise PermissionError('simulated unavailable proc')
            return original_open(path, *args, **kwargs)

        def unavailable_proc_directory(path='.', *args, **kwargs):
            if str(path).startswith('/proc'):
                raise PermissionError('simulated unavailable proc')
            return original_listdir(path, *args, **kwargs)

        with mock.patch('builtins.open', side_effect=unavailable_proc), \
                mock.patch('os.listdir', side_effect=unavailable_proc_directory):
            result = client.run([sys.executable, '-c', producer], cwd=self.root,
                                env=dict(self.env, OWNED_CONTROL_VALUE='kept'), timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        for parent in [value['parent'], value['scene']['parent'], value['scene']['engine']['parent']]:
            self.assertEqual(parent, os.getpid())
        self.assertEqual(value['scene']['engine']['arg'], 'space and unicode λ')
        self.assertEqual(value['scene']['engine']['value'], 'kept')
        self.assertEqual(result.stderr, b'engine stderr\n')
        self.assertEqual(len(self.broker.receipts), 3)
        self.assertTrue(all(r['pidfd_registered'] and r['waited'] for r in self.broker.receipts))
        self.assertEqual(sum(not r['parent'] for r in self.broker.receipts), 1)

    def test_immediate_exit_and_nonzero_status_are_actual_wait_results(self):
        result = self.run_fake("import os; os._exit(17)")
        self.assertEqual(result.returncode, 17)
        self.assertTrue(result.owned_receipt['waited'])
        self.assertTrue(result.owned_receipt['gate_released'])

    def test_exec_failure_remains_nonzero_with_diagnostic(self):
        result = client.run([str(self.root / 'absent-executable')], env=self.env, timeout=3)
        self.assertEqual(result.returncode, 127)
        self.assertIn(b'owned target exec failed', result.stderr)
        self.assertTrue(result.owned_receipt['waited'])

    def test_registration_refusal_never_runs_target_and_waits_for_closed_gate(self):
        marker = self.root / 'must-not-exist'
        self.env['LD_PRELOAD'] = str(self.root / 'untrusted-target-only.so')
        original_popen = subprocess.Popen
        with mock.patch('os.pidfd_open', side_effect=OSError('registration refused')), \
                mock.patch('subprocess.Popen', wraps=original_popen) as bootstrap:
            with self.assertRaises(client.OwnedLaunchError):
                self.run_fake(f"from pathlib import Path;Path({str(marker)!r}).touch()")
            self.assertNotIn('LD_PRELOAD', bootstrap.call_args.kwargs['env'])
        self.assertFalse(marker.exists())
        self.assertFalse(self.broker.jobs)
        self.assertTrue(self.broker.receipts[-1]['waited'])
        self.assertFalse(self.broker.receipts[-1]['pidfd_registered'])
        self.assertFalse(self.broker.receipts[-1]['gate_released'])

    def test_cancel_while_gate_closed_refuses_target_exec(self):
        entered, release = threading.Event(), threading.Event()
        self.broker._before_release = lambda _identity: (entered.set(), release.wait(2))
        marker = self.root / 'gate-target-must-not-exist'
        results = []

        def request():
            try:
                results.append(self.run_fake(f"from pathlib import Path;Path({str(marker)!r}).touch()"))
            except OSError as exc:
                results.append(exc)

        worker = threading.Thread(target=request)
        worker.start()
        self.assertTrue(entered.wait(2))
        self.broker.cancel()
        release.set()
        worker.join(6)
        self.assertFalse(worker.is_alive())
        self.assertFalse(marker.exists())
        self.assertFalse(self.broker.jobs)
        self.assertFalse(self.broker.receipts[-1]['gate_released'])

    def test_nested_cancellation_collects_all_registered_children(self):
        marker = self.root / 'nested-active'
        child = f"from pathlib import Path;import time;Path({str(marker)!r}).touch();time.sleep(10)"
        parent = ("import sys,os\nfrom scripts.review import owned_launch as c\n"
                  f"c.run([sys.executable,'-c',{child!r}],env=os.environ,timeout=12)\n")
        errors = []

        def request():
            try:
                self.run_fake(parent, timeout=15)
            except (OSError, subprocess.SubprocessError) as exc:
                errors.append(exc)

        worker = threading.Thread(target=request)
        worker.start()
        self.wait_file(marker)
        self.broker.cancel()
        worker.join(6)
        self.assertFalse(worker.is_alive())
        self.assertFalse(self.broker.jobs)
        self.assertEqual(len(self.broker.receipts), 2)
        self.assertTrue(all(r['waited'] and r['returncode'] != 0 for r in self.broker.receipts))

    def test_timeout_keeps_bounded_output_and_refuses_late_requests(self):
        with self.assertRaises(subprocess.TimeoutExpired) as caught:
            self.run_fake("import sys,time;print('before timeout',flush=True);"
                          "print('stderr prefix',file=sys.stderr,flush=True);time.sleep(10)", timeout=0.3)
        self.assertIn(b'before timeout', caught.exception.output)
        self.assertIn(b'stderr prefix', caught.exception.stderr)
        self.assertFalse(self.broker.jobs)
        with mock.patch('subprocess.Popen') as local:
            with self.assertRaises(client.OwnedLaunchError):
                self.run_fake("print('late launch must not execute')")
            local.assert_not_called()

    def test_duplicate_request_cannot_execute_target_twice(self):
        marker = self.root / 'once.txt'
        code = f"from pathlib import Path;p=Path({str(marker)!r});p.write_text(p.read_text()+'x' if p.exists() else 'x')"
        request = dict(op='launch', request_id='one-logical-request', parent='',
                       args=[sys.executable, '-c', code], cwd=str(self.root), env=self.env, timeout=3)
        client._request(request, self.env, 3)
        with self.assertRaises(client.OwnedLaunchError):
            client._request(request, self.env, 3)
        self.assertEqual(marker.read_text(), 'x')

    def test_broken_client_channel_cancels_and_reaps_registered_job(self):
        marker = self.root / 'channel-started'
        code = f"from pathlib import Path;import time;Path({str(marker)!r}).touch();time.sleep(10)"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:
            channel.connect(str(self.broker.socket_path))
            client._send(channel, dict(op='launch', token=self.broker.token, request_id='broken-channel',
                                      parent='', args=[sys.executable, '-c', code], cwd=str(self.root),
                                      env=self.env, timeout=12), client.MAX_REQUEST)
            self.wait_file(marker)
        deadline = time.monotonic() + 5
        while self.broker.jobs and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(self.broker.jobs)
        self.assertTrue(self.broker.cancelled)
        self.assertTrue(self.broker.receipts[-1]['waited'])

    def test_missing_broker_credentials_and_connection_never_fall_back(self):
        for env in [{client.SOCKET_ENV: str(self.root / 'absent.sock')},
                    {client.SOCKET_ENV: str(self.root / 'absent.sock'), client.TOKEN_ENV: 'invalid'}]:
            with mock.patch('subprocess.Popen') as local:
                with self.assertRaises(client.OwnedLaunchError):
                    client.run([sys.executable, '-c', "print('forbidden')"], env=env, timeout=1)
                local.assert_not_called()

    def test_stdout_stderr_text_and_checked_status_match_capture_contract(self):
        result = self.run_fake("import sys;print('stdout λ');print('stderr',file=sys.stderr);sys.exit(3)", text=True)
        self.assertEqual((result.stdout, result.stderr, result.returncode), ('stdout λ\n', 'stderr\n', 3))
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            self.run_fake("import sys;print('kept');sys.exit(4)", check=True)
        self.assertEqual(caught.exception.returncode, 4)
        self.assertEqual(caught.exception.output, b'kept\n')

    def test_output_limit_fails_instead_of_returning_success(self):
        with self.assertRaises(client.OwnedLaunchError):
            self.run_fake(f"import sys;sys.stdout.write('x'*{client.MAX_OUTPUT + 65536});sys.stdout.flush()")
        self.assertFalse(self.broker.jobs)
        self.assertTrue(self.broker.cancelled)

    def test_unregistered_native_descendant_is_explicitly_not_covered(self):
        code = ("import subprocess,sys,os,json\n"
                "r=subprocess.run([sys.executable,'-c','import os;print(os.getppid())'],capture_output=True,text=True)\n"
                "print(json.dumps({'pid':os.getpid(),'child_parent':int(r.stdout)}))\n")
        result = self.run_fake(code)
        value = json.loads(result.stdout)
        self.assertEqual(value['child_parent'], value['pid'])
        self.assertNotEqual(value['child_parent'], os.getpid())
        self.assertEqual(len(self.broker.receipts), 1)
        self.assertIn('native descendants/RSS unmeasured', result.owned_receipt['coverage'])


if __name__ == '__main__':
    unittest.main()
