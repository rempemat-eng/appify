"""Y47 focused controls, AUTHORED BUT UNRUN under source-only GO6503275523.

Future allocation must execute every method with real Linux pidfds, tiny private
fake producers only, and retain errors/capability refusals rather than skips.
No engine, display, project assets or /proc namespace setup is used here.
"""
from __future__ import annotations

import builtins
import contextlib
import json
import os
from pathlib import Path
import socket
import signal
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from . import owned_launch as client
from .owned_broker import Broker, _ServiceBroker, _actual_wait, _child_policy


@contextlib.contextmanager
def fixture_broker(root, setup):
    """Only test source can substitute a tiny dedicated service bootstrap.

    Production Broker has no fixture/callback/module-injection parameter.
    """
    fixture = root / 'fixture_service.py'
    tools = str(Path(__file__).resolve().parents[2])
    fixture.write_text(
        "import sys\nfrom pathlib import Path\nsys.path.insert(0," + repr(tools) + ")\n"
        "from scripts.review import owned_broker as b\n" + setup + "\n"
        "raise SystemExit(b._service_main(sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5])))\n")
    original = subprocess.Popen
    def launch(argv, **kwargs):
        argv = list(argv)
        if '--service' in argv:
            argv[4] = str(fixture)
        return original(argv, **kwargs)
    with mock.patch('subprocess.Popen', side_effect=launch):
        with Broker(root / 'fixture-broker') as broker:
            yield broker


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

    def wait_collected(self, broker, seconds=6):
        deadline = time.monotonic() + seconds
        while broker.jobs and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertFalse(broker.jobs, 'actual service waits did not finish in bound')

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
            self.assertEqual(parent, self.broker.service_pid)
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
        setup = "def refuse(*a,**k): raise OSError('registration refused')\nb.os.pidfd_open=refuse"
        with fixture_broker(self.root, setup) as broker:
            env = broker.environment(dict(os.environ, LD_PRELOAD=str(self.root / 'untrusted.so')))
            with self.assertRaises(client.OwnedLaunchError):
                client.run([sys.executable, '-c', f"from pathlib import Path;Path({str(marker)!r}).touch()"],
                           env=env, timeout=3)
            self.assertFalse(marker.exists())
            self.assertFalse(broker.jobs)
            self.assertTrue(broker.receipts[-1]['waited'])
            self.assertFalse(broker.receipts[-1]['pidfd_registered'])
            self.assertFalse(broker.receipts[-1]['gate_released'])

    def test_cancel_while_gate_closed_refuses_target_exec(self):
        marker, entered, release = (self.root / n for n in ('no-target', 'at-gate', 'release-gate'))
        setup = ("import time\n"
                 "def hold(self,identity):\n"
                 f" Path({str(entered)!r}).touch()\n"
                 " deadline=time.monotonic()+3\n"
                 f" while not Path({str(release)!r}).exists() and time.monotonic()<deadline: time.sleep(.01)\n"
                 "b._ServiceBroker._before_release=hold")
        with fixture_broker(self.root, setup) as broker:
            errors = []
            def request():
                try:
                    client.run([sys.executable,'-c',f"from pathlib import Path;Path({str(marker)!r}).touch()"],
                               env=broker.environment(), timeout=4)
                except OSError as exc:
                    errors.append(exc)
            worker = threading.Thread(target=request)
            worker.start()
            self.wait_file(entered)
            broker.cancel()
            release.touch()
            worker.join(6)
            self.assertFalse(worker.is_alive())
            self.assertTrue(errors)
            self.assertFalse(marker.exists())
            self.wait_collected(broker)
            self.assertFalse(broker.receipts[-1]['gate_released'])

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
        self.wait_collected(self.broker)
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
        code = "import os;os.write(1,b'a\\r\\nb\\rc\\n');os.write(2,b'e\\r\\nf\\r');raise SystemExit(3)"
        for options in ({'text': True}, {'errors': 'replace'}, {'encoding': 'utf-8'}):
            expected = subprocess.run([sys.executable, '-c', code], capture_output=True, **options)
            result = self.run_fake(code, **options)
            self.assertEqual((result.stdout, result.stderr, result.returncode),
                             (expected.stdout, expected.stderr, expected.returncode))
            self.assertEqual((result.stdout, result.stderr), ('a\nb\nc\n', 'e\nf\n'))
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            self.run_fake("print('kept');raise SystemExit(4)", check=True)
        self.assertEqual(caught.exception.output, b'kept\n')

    def test_ignored_sigchld_refuses_before_any_service_spawn(self):
        with mock.patch('signal.getsignal', return_value=signal.SIG_IGN), \
                mock.patch('subprocess.Popen') as spawn:
            with self.assertRaises(client.OwnedLaunchError):
                Broker(self.root / 'ignored').__enter__()
            spawn.assert_not_called()

    def test_unsupported_reaper_abi_refuses_before_spawn(self):
        with mock.patch('platform.machine', return_value='unsupported'), \
                mock.patch('subprocess.Popen') as spawn:
            with self.assertRaises(client.OwnedLaunchError):
                Broker(self.root / 'unsupported').__enter__()
            spawn.assert_not_called()

    def test_inprocess_service_without_exclusive_authority_refuses(self):
        with mock.patch('subprocess.Popen') as spawn:
            with self.assertRaises(client.OwnedLaunchError):
                _ServiceBroker(self.root / 'no-authority').__enter__()
            spawn.assert_not_called()

    def test_lost_kernel_wait_never_becomes_synthetic_success(self):
        process = mock.Mock(pid=123, returncode=None, args=['unrun-control'])
        process._waitpid_lock = threading.Lock()
        process._owned_wait_lost = False
        with mock.patch('os.waitpid', side_effect=ChildProcessError()):
            with self.assertRaisesRegex(client.OwnedLaunchError, 'ECHILD'):
                _actual_wait(process)
        self.assertIsNone(process.returncode)
        self.assertTrue(process._owned_wait_lost)

    def test_nocldwait_refuses_before_any_service_spawn(self):
        def query(_sig, _new, old):
            old._obj.handler = None
            old._obj.flags = 2  # Linux x86_64 SA_NOCLDWAIT
            return 0
        libc = mock.Mock()
        libc.sigaction = query
        with mock.patch('ctypes.CDLL', return_value=libc), \
                mock.patch('signal.getsignal', return_value=signal.SIG_DFL), \
                mock.patch('subprocess.Popen') as spawn:
            with self.assertRaises(client.OwnedLaunchError):
                Broker(self.root / 'auto-reap').__enter__()
            spawn.assert_not_called()

    def test_partial_frame_absolute_deadline_ignores_drip_progress(self):
        left, right = socket.socketpair()
        stop = threading.Event()
        def drip():
            try:
                right.sendall(struct.pack('!I', 200))
                while not stop.wait(.025):
                    right.sendall(b' ')
            except OSError:
                pass
        worker = threading.Thread(target=drip)
        worker.start()
        try:
            started = time.monotonic()
            with self.assertRaises((client.OwnedLaunchError, socket.timeout)):
                client._receive(left, client.MAX_REQUEST, deadline=started + .15)
            self.assertLess(time.monotonic() - started, .8)
        finally:
            stop.set()
            left.close()
            right.close()
            worker.join(1)
            self.assertFalse(worker.is_alive())

    def test_partial_frame_cancellation_collects_prelaunch_handler(self):
        with Broker(self.root / 'partial-frame-broker') as broker:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:
                channel.connect(str(broker.socket_path))
                channel.sendall(struct.pack('!I', 200) + b'{')
                started = time.monotonic()
                broker.cancel()
        self.assertLess(time.monotonic() - started, 4)
        self.assertFalse(broker.jobs)
        self.assertEqual(broker.receipts, [])

    def test_repeated_cancel_preserves_control_reply_and_raw_collection(self):
        for _ in range(3):
            self.assertTrue(self.broker.cancel()['cancelled'])
        self.assertTrue(self.broker.cancelled)
        self.assertFalse(self.broker.jobs)
        self.assertEqual(self.broker.receipts, [])

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
        self.assertNotEqual(value['child_parent'], self.broker.service_pid)
        self.assertEqual(len(self.broker.receipts), 1)
        self.assertIn('native descendants/RSS unmeasured', result.owned_receipt['coverage'])


if __name__ == '__main__':
    unittest.main()
