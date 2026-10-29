"""External-controller component for explicitly registered Y12 launches.

The broker process is the actual parent, holds pidfds until wait completion and
releases a trusted exec gate only after registration. This is not a sandbox,
global RSS monitor or accounting for arbitrary native grandchildren.
Runtime/pidfd/process controls are source-prepared and require separate GO.
"""
from __future__ import annotations

import base64
import json
import math
import os
from pathlib import Path
import secrets
import selectors
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time

from . import owned_launch as client

MAX_JOBS = 32
MAX_REQUEST_IDS = 4096
MAX_CONNECTIONS = 4096


class Broker:
    """One controller-owned allocation. Use a NEW private directory per instance."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.socket_path = self.root / 'launch.sock'
        self.token = secrets.token_hex(32)
        self.lock = threading.RLock()
        self.cancelled = False
        self.stopping = threading.Event()
        self.jobs = {}
        self.seen = set()
        self.receipts = []
        self.collection_errors = []
        self.workers = []
        self.slots = threading.BoundedSemaphore(MAX_JOBS)

    def __enter__(self):
        if not hasattr(os, 'pidfd_open') or not hasattr(signal, 'pidfd_send_signal'):
            raise client.OwnedLaunchError('pidfd registration/signalling unavailable; no fallback')
        self.root.mkdir(mode=0o700, parents=False, exist_ok=False)
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.server.bind(str(self.socket_path))
            os.chmod(self.socket_path, 0o600)
            self.server.listen(MAX_JOBS)
            self.server.settimeout(0.1)
            self.thread = threading.Thread(target=self._serve, daemon=True)
            self.thread.start()
        except BaseException:
            self.server.close()
            raise
        return self

    def environment(self, base=None):
        return dict(os.environ if base is None else base,
                    **{client.SOCKET_ENV: str(self.socket_path),
                       client.TOKEN_ENV: self.token, client.PARENT_ENV: ''})

    def _signal(self, job):
        # Caller holds lock; fd cannot be closed/reused until this returns.
        if job['pidfd'] is not None:
            try:
                signal.pidfd_send_signal(job['pidfd'], signal.SIGKILL)
            except ProcessLookupError:
                pass

    def cancel(self):
        with self.lock:
            self.cancelled = True
            failures = []
            for identity, job in self.jobs.items():
                if job['gate'] is not None:
                    os.close(job['gate'])
                    job['gate'] = None
                try:
                    self._signal(job)
                except OSError as exc:
                    failures.append(identity + ': pidfd signal failed: ' + str(exc))
            self.collection_errors.extend(failures)
            if failures:
                raise client.OwnedLaunchError('; '.join(failures))

    def __exit__(self, *_exc):
        self.stopping.set()
        self.cancel()
        self.thread.join(timeout=2)
        self.server.close()
        for worker in self.workers:
            worker.join(timeout=6)
        if (self.thread.is_alive() or any(worker.is_alive() for worker in self.workers)
                or self.jobs or self.collection_errors):
            raise client.OwnedLaunchError('registered launch collection did not terminate')
        # Only our named socket is removed; reports/private root remain for inspection.
        self.socket_path.unlink(missing_ok=True)

    def _serve(self):
        accepted = 0
        while not self.stopping.is_set():
            try:
                channel, _ = self.server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            if self.stopping.is_set():
                channel.close()
                break
            accepted += 1
            if accepted > MAX_CONNECTIONS:
                channel.close()
                self.cancel()
                break
            self.workers = [worker for worker in self.workers if worker.is_alive()]
            if not self.slots.acquire(blocking=False):
                channel.close()
                continue
            worker = threading.Thread(target=self._handle, args=(channel,), daemon=True)
            self.workers.append(worker)
            worker.start()

    def _handle(self, channel):
        try:
            with channel:
                channel.settimeout(2)
                try:
                    request = client._receive(channel, client.MAX_REQUEST)
                    if not secrets.compare_digest(str(request.get('token', '')), self.token):
                        raise client.OwnedLaunchError('broker authentication refused')
                    if request.get('op') == 'cancel':
                        self.cancel()
                        response = {'cancelled': True}
                    elif request.get('op') == 'launch':
                        response = self._launch(request, channel)
                    else:
                        raise client.OwnedLaunchError('unsupported broker operation')
                except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
                    response = {'error': str(exc)}
                try:
                    channel.settimeout(2)
                    client._send(channel, response, client.MAX_REPLY)
                except (OSError, ValueError, TypeError):
                    # A missing consumer is not permission to keep producing work.
                    self.cancel()
        finally:
            self.slots.release()

    def _validate(self, request):
        args, env = request.get('args'), request.get('env')
        request_id, parent = request.get('request_id'), request.get('parent', '')
        timeout = request.get('timeout')
        if (not isinstance(request_id, str) or not 1 <= len(request_id) <= 64
                or not isinstance(parent, str) or len(parent) > 64):
            raise client.OwnedLaunchError('invalid logical launch identity')
        if (not isinstance(args, list) or not args or len(args) > 256
                or any(not isinstance(a, str) or '\x00' in a for a in args)):
            raise client.OwnedLaunchError('invalid target argv')
        if (not isinstance(env, dict) or len(env) > 2048
                or any(not isinstance(k, str) or not k or '=' in k or '\x00' in k
                       or not isinstance(v, str) or '\x00' in v for k, v in env.items())):
            raise client.OwnedLaunchError('invalid target environment')
        if (type(timeout) not in (int, float) or not math.isfinite(timeout)
                or not 0 < timeout <= client.MAX_TIMEOUT):
            raise client.OwnedLaunchError('invalid timeout')
        cwd = request.get('cwd')
        if not isinstance(cwd, str) or not os.path.isabs(cwd) or not Path(cwd).is_dir():
            raise client.OwnedLaunchError('invalid target cwd')
        with self.lock:
            if self.cancelled or self.stopping.is_set():
                raise client.OwnedLaunchError('allocation cancelled; late launch refused')
            if request_id in self.seen or len(self.seen) >= MAX_REQUEST_IDS:
                raise client.OwnedLaunchError('duplicate/exhausted logical request identity')
            if parent and (parent not in self.jobs or self.jobs[parent]['process'].poll() is not None):
                raise client.OwnedLaunchError('nested launch lacks an active registered parent')
            self.seen.add(request_id)
        return request_id, parent, args, dict(env), cwd, timeout

    def _before_release(self, _request_id):
        """Static review/test seam; default has no process or timing side effects."""

    def _launch(self, request, channel):
        request_id, parent, args, env, cwd, timeout = self._validate(request)
        env.update({client.SOCKET_ENV: str(self.socket_path), client.TOKEN_ENV: self.token,
                    client.PARENT_ENV: request_id})
        gate_read, gate_write = os.pipe()
        process = None
        job = dict(pidfd=None, gate=gate_write, process=None)
        registered = released = waited = False
        started = time.monotonic()
        try:
            with tempfile.TemporaryFile(dir=self.root) as spec:
                spec.write(json.dumps(dict(args=args, env=env), allow_nan=False).encode())
                spec.flush()
                spec.seek(0)
                process = subprocess.Popen(
                    [sys.executable, '-I', '-B', str(Path(client.__file__).resolve()),
                     '--gate', str(gate_read), str(spec.fileno())],
                    # Target-controlled loader/Python environment is applied ONLY
                    # by execvpe after registration, never to the trusted gate.
                    cwd=cwd, env={'PATH': os.defpath, 'LANG': 'C.UTF-8'}, stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    pass_fds=(gate_read, spec.fileno()), close_fds=True)
            os.close(gate_read)
            gate_read = None
            job['process'] = process
            # The trusted helper cannot exec the target while this gate is closed.
            job['pidfd'] = os.pidfd_open(process.pid, 0)
            registered = True
            with self.lock:
                self.jobs[request_id] = job
            self._before_release(request_id)
            with self.lock:
                if self.cancelled:
                    self._signal(job)
                else:
                    os.write(job['gate'], b'1')
                    released = True
                if job['gate'] is not None:
                    os.close(job['gate'])
                    job['gate'] = None
            stdout, stderr, timed_out, error = self._collect(process, channel, job, timeout, started)
            code = process.wait(timeout=5)
            waited = True
            receipt = dict(request_id=request_id, parent=parent, pidfd_registered=registered,
                           gate_released=released, waited=waited, returncode=code,
                           coverage='registered direct children only; native descendants/RSS unmeasured')
            with self.lock:
                self.receipts.append(receipt)
            result = dict(returncode=code, stdout=base64.b64encode(stdout).decode(),
                          stderr=base64.b64encode(stderr).decode(), receipt=receipt,
                          timed_out=timed_out)
            if error:
                result['error'] = error
            return result
        finally:
            if gate_read is not None:
                os.close(gate_read)
            with self.lock:
                if job['gate'] is not None:
                    os.close(job['gate'])
                    job['gate'] = None
                if process is not None and process.poll() is None and registered:
                    self._signal(job)
            cleanup_waited = process is None
            if process is not None:
                # Registration refusal closes the gate: only trusted helper code ran.
                # No PID/PGID fallback even if pidfd_open failed.
                try:
                    cleanup_code = process.wait(timeout=5)
                    cleanup_waited = True
                    if not waited:
                        with self.lock:
                            self.receipts.append(dict(request_id=request_id, parent=parent,
                                                      pidfd_registered=registered,
                                                      gate_released=released, waited=True,
                                                      returncode=cleanup_code,
                                                      outcome='launch/collection failed'))
                except subprocess.TimeoutExpired:
                    with self.lock:
                        self.collection_errors.append(request_id + ': child wait incomplete')
                        self.jobs[request_id] = job
                finally:
                    for stream in (process.stdout, process.stderr):
                        stream.close()
            with self.lock:
                if cleanup_waited:
                    self.jobs.pop(request_id, None)
                    if job['pidfd'] is not None:
                        os.close(job['pidfd'])
                        job['pidfd'] = None

    def _collect(self, process, channel, job, timeout, started):
        output = [bytearray(), bytearray()]
        timed_out, error = False, None
        drain_deadline = None
        channel.setblocking(False)
        with selectors.DefaultSelector() as selector:
            for i, stream in enumerate((process.stdout, process.stderr)):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, i)
            while selector.get_map() or process.poll() is None:
                if drain_deadline is None and time.monotonic() - started > timeout:
                    timed_out = True
                    self.cancel()
                    drain_deadline = time.monotonic() + 3
                if self.cancelled and drain_deadline is None:
                    drain_deadline = time.monotonic() + 3
                if drain_deadline is not None and time.monotonic() > drain_deadline:
                    # An unregistered native descendant may hold inherited pipes.
                    error = 'registered process cancelled; output drain incomplete (unregistered descendant possible)'
                    break
                try:
                    if drain_deadline is None and channel.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT) == b'':
                        error = 'owned client disconnected'
                        self.cancel()
                        drain_deadline = time.monotonic() + 3
                except BlockingIOError:
                    pass
                # socket timeout mode must not turn this nonblocking probe into a wait.
                except socket.timeout:
                    pass
                for key, _ in selector.select(0.02):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    elif sum(map(len, output)) + len(chunk) > client.MAX_OUTPUT:
                        error = 'owned captured output exceeds its bound'
                        self.cancel()
                        if drain_deadline is None:
                            drain_deadline = time.monotonic() + 3
                    else:
                        output[key.data].extend(chunk)
        return bytes(output[0]), bytes(output[1]), timed_out, error
