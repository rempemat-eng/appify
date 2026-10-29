"""External-controller component for explicitly registered Y12 launches.

The broker process is the actual parent, holds pidfds until wait completion and
releases a trusted exec gate only after registration. This is not a sandbox,
global RSS monitor or accounting for arbitrary native grandchildren.
Runtime/pidfd/process controls are source-prepared and require separate GO.
"""
from __future__ import annotations

import base64
import ctypes
import platform
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

if __package__:
    from . import owned_launch as client
else:
    # Only the reviewed tool tree is importable in the isolated service.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.review import owned_launch as client

MAX_JOBS = 32
MAX_REQUEST_IDS = 4096
MAX_CONNECTIONS = 4096


_SERVICE_AUTHORITY = None


def _child_policy():
    """Query the supported Linux/glibc sigaction ABI; no guessed fallback."""
    if (sys.platform != 'linux' or platform.machine() != 'x86_64'
            or ctypes.sizeof(ctypes.c_void_p) != 8 or ctypes.sizeof(ctypes.c_ulong) != 8):
        raise client.OwnedLaunchError('exclusive reaper requires Linux x86_64 glibc')
    libc = ctypes.CDLL(None, use_errno=True)
    if not hasattr(libc, 'gnu_get_libc_version'):
        raise client.OwnedLaunchError('unsupported sigaction ABI')
    class Sigaction(ctypes.Structure):
        _fields_ = [('handler', ctypes.c_void_p), ('mask', ctypes.c_ulong * 16),
                    ('flags', ctypes.c_int), ('restorer', ctypes.c_void_p)]
    if ctypes.sizeof(Sigaction) != 152 or Sigaction.flags.offset != 136:
        raise client.OwnedLaunchError('unsupported sigaction structure layout')
    query = libc.sigaction
    query.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(Sigaction)]
    query.restype = ctypes.c_int
    action = Sigaction()
    if (query(signal.SIGCHLD, None, ctypes.byref(action)) != 0
            or action.handler is not None or action.flags & 2
            or signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL):
        raise client.OwnedLaunchError('SIGCHLD must be default, without SA_NOCLDWAIT')


def _actual_wait(process, *, timeout=0):
    """Never use Popen.poll/wait: ECHILD is lost evidence, not status zero."""
    with process._waitpid_lock:
        if getattr(process, '_owned_wait_lost', False):
            raise client.OwnedLaunchError('actual kernel child wait previously lost')
        if process.returncode is not None:
            return process.returncode
        deadline = time.monotonic() + timeout
        while True:
            try:
                pid, status = os.waitpid(process.pid, os.WNOHANG)
            except InterruptedError:
                continue
            except ChildProcessError as exc:
                process._owned_wait_lost = True
                raise client.OwnedLaunchError('actual kernel child wait lost (ECHILD)') from exc
            if pid == process.pid:
                process.returncode = os.waitstatus_to_exitcode(status)
                return process.returncode
            if pid != 0:
                process._owned_wait_lost = True
                raise client.OwnedLaunchError('unexpected kernel child wait identity')
            if time.monotonic() >= deadline:
                if timeout:
                    raise subprocess.TimeoutExpired(process.args, timeout)
                return None
            time.sleep(0.01)



class _ServiceBroker:
    """One controller-owned allocation. Use a NEW private directory per instance."""

    def __init__(self, root, *, authority=None):
        self.authority = authority
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
        self.channels = set()
        self.slots = threading.BoundedSemaphore(MAX_JOBS)

    def __enter__(self):
        if self.authority is None or self.authority is not _SERVICE_AUTHORITY:
            raise client.OwnedLaunchError('broker requires its dedicated isolated service')
        _child_policy()
        if not hasattr(os, 'pidfd_open') or not hasattr(signal, 'pidfd_send_signal'):
            raise client.OwnedLaunchError('pidfd registration/signalling unavailable; no fallback')
        if not self.root.is_dir():
            raise client.OwnedLaunchError('private broker root missing')
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
        if job['process'] is not None and getattr(job['process'], '_owned_wait_lost', False):
            raise client.OwnedLaunchError('signal refused after lost actual wait')
        if job['pidfd'] is not None:
            try:
                signal.pidfd_send_signal(job['pidfd'], signal.SIGKILL)
            except ProcessLookupError:
                pass

    def cancel(self, exclude=None):
        with self.lock:
            # First cancellation owns the channel shutdown. A cancelled launch
            # must not close the still-in-flight control RPC response on reentry.
            if self.cancelled:
                return
            self.cancelled = True
            failures = []
            for channel in tuple(self.channels):
                if channel is exclude:
                    continue
                try:
                    channel.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
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
        try:
            self.cancel()
        finally:
            self.server.close()
            deadline = time.monotonic() + 8
            self.thread.join(timeout=max(0, deadline - time.monotonic()))
            for worker in self.workers:
                worker.join(timeout=max(0, deadline - time.monotonic()))
        if (self.thread.is_alive() or any(worker.is_alive() for worker in self.workers)
                or self.jobs or self.collection_errors):
            raise client.OwnedLaunchError('registered launch collection did not terminate')
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
            with self.lock:
                if self.stopping.is_set():
                    channel.close()
                    self.slots.release()
                    continue
                self.channels.add(channel)
            worker = threading.Thread(target=self._handle, args=(channel,), daemon=True)
            self.workers.append(worker)
            worker.start()

    def _handle(self, channel):
        try:
            with channel:
                channel.settimeout(2)
                try:
                    request = client._receive(channel, client.MAX_REQUEST,
                                              deadline=time.monotonic() + 2)
                    if not secrets.compare_digest(str(request.get('token', '')), self.token):
                        raise client.OwnedLaunchError('broker authentication refused')
                    if request.get('op') == 'cancel':
                        self.cancel(exclude=channel)
                        response = {'cancelled': True}
                    elif request.get('op') == 'snapshot':
                        with self.lock:
                            response = dict(receipts=list(self.receipts), jobs=list(self.jobs),
                                            collection_errors=list(self.collection_errors),
                                            cancelled=self.cancelled, pid=os.getpid())
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
            with self.lock:
                self.channels.discard(channel)
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
            if parent and (parent not in self.jobs or _actual_wait(self.jobs[parent]['process']) is not None):
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
            # Only trusted service threads exist here; no user callbacks/modules.
            # Recheck the kernel disposition immediately before each spawn.
            _child_policy()
            with tempfile.TemporaryFile(dir=self.root) as spec:
                spec.write(json.dumps(dict(args=args, env=env), allow_nan=False).encode())
                spec.flush()
                spec.seek(0)
                process = subprocess.Popen(
                    [sys.executable, '-I', '-S', '-B', str(Path(client.__file__).resolve()),
                     '--gate', str(gate_read), str(spec.fileno())],
                    # Target-controlled loader/Python environment is applied ONLY
                    # by execvpe after registration, never to the trusted gate.
                    cwd=cwd, env={'PATH': os.defpath, 'LANG': 'C.UTF-8'}, stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    pass_fds=(gate_read, spec.fileno()), close_fds=True)
            os.close(gate_read)
            gate_read = None
            job['process'] = process
            with self.lock:
                self.jobs[request_id] = job
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
            code = _actual_wait(process, timeout=5)
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
                if process is not None and registered and not getattr(process, '_owned_wait_lost', False):
                    self._signal(job)
            cleanup_waited = process is None
            if process is not None:
                # Registration refusal closes the gate: only trusted helper code ran.
                # No PID/PGID fallback even if pidfd_open failed.
                try:
                    cleanup_code = _actual_wait(process, timeout=5)
                    cleanup_waited = True
                    if not waited:
                        with self.lock:
                            self.receipts.append(dict(request_id=request_id, parent=parent,
                                                      pidfd_registered=registered,
                                                      gate_released=released, waited=True,
                                                      returncode=cleanup_code,
                                                      outcome='launch/collection failed'))
                except (subprocess.TimeoutExpired, client.OwnedLaunchError):
                    with self.lock:
                        self.collection_errors.append(request_id + ': actual child wait incomplete/lost')
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
            while selector.get_map() or _actual_wait(process) is None:
                if drain_deadline is None and time.monotonic() - started > timeout:
                    timed_out = True
                    self.cancel(exclude=channel)
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
                        self.cancel(exclude=channel)
                        drain_deadline = time.monotonic() + 3
                except BlockingIOError:
                    pass
                except OSError:
                    error = 'owned client channel cancelled'
                    self.cancel(exclude=channel)
                    if drain_deadline is None:
                        drain_deadline = time.monotonic() + 3
                # socket timeout mode must not turn this nonblocking probe into a wait.
                except socket.timeout:
                    pass
                for key, _ in selector.select(0.02):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    elif sum(map(len, output)) + len(chunk) > client.MAX_OUTPUT:
                        error = 'owned captured output exceeds its bound'
                        self.cancel(exclude=channel)
                        if drain_deadline is None:
                            drain_deadline = time.monotonic() + 3
                    else:
                        output[key.data].extend(chunk)
        return bytes(output[0]), bytes(output[1]), timed_out, error


class Broker:
    """Controller facade; all managed targets are children of a dedicated service.

    The service imports no target/controller callbacks or user modules. Its only
    reaper is _actual_wait, retaining zombies until post-spawn pidfd binding.
    """
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.socket_path = self.root / 'launch.sock'
        self.token = secrets.token_hex(32)
        self.process = None
        self.owner = None
        self.final_snapshot = None

    def __enter__(self):
        # Refuse a controller auto-reap disposition before spawning even the service.
        _child_policy()
        self.root.mkdir(mode=0o700, parents=False, exist_ok=False)
        ready_read, ready_write = os.pipe()
        owner_read, self.owner = os.pipe()
        try:
            with (self.root / 'service.log').open('xb') as log:
                self.process = subprocess.Popen(
                    [sys.executable, '-I', '-S', '-B', str(Path(__file__).resolve()),
                     '--service', str(self.root), self.token, str(ready_write), str(owner_read)],
                    env={'PATH': os.defpath, 'LANG': 'C.UTF-8'}, cwd=self.root,
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=log,
                    pass_fds=(ready_write, owner_read), close_fds=True)
            with selectors.DefaultSelector() as selector:
                selector.register(ready_read, selectors.EVENT_READ)
                if not selector.select(5) or os.read(ready_read, 1) != b'R':
                    raise client.OwnedLaunchError('dedicated broker service startup refused')
        except BaseException:
            if self.owner is not None:
                os.close(self.owner)
                self.owner = None
            if self.process is not None:
                _actual_wait(self.process, timeout=8)
            raise
        finally:
            for fd in (ready_read, ready_write, owner_read):
                os.close(fd)
        return self

    @property
    def service_pid(self):
        return self.process.pid

    def environment(self, base=None):
        return dict(os.environ if base is None else base,
                    **{client.SOCKET_ENV: str(self.socket_path),
                       client.TOKEN_ENV: self.token, client.PARENT_ENV: ''})

    def _snapshot(self):
        if self.final_snapshot is not None:
            return self.final_snapshot
        return client._request({'op': 'snapshot'}, self.environment(), 5)

    @property
    def jobs(self):
        return self._snapshot()['jobs']

    @property
    def receipts(self):
        return self._snapshot()['receipts']

    @property
    def cancelled(self):
        return self._snapshot()['cancelled']

    def cancel(self):
        return client.cancel(self.environment())

    def __exit__(self, *_exc):
        failure = None
        try:
            self.cancel()
        except OSError as exc:
            failure = exc
        finally:
            if self.owner is not None:
                os.close(self.owner)
                self.owner = None
        code = _actual_wait(self.process, timeout=12)
        result = self.root / 'service-final.json'
        if result.is_file():
            self.final_snapshot = json.loads(result.read_text())
        if (failure is not None or code != 0 or self.final_snapshot is None
                or self.final_snapshot['jobs'] or self.final_snapshot['collection_errors']):
            raise client.OwnedLaunchError('dedicated broker service collection failed') from failure


def _service_main(root, token, ready_fd, owner_fd):
    global _SERVICE_AUTHORITY
    # Fresh -I -S interpreter, trusted imports only. No external controller can
    # reap its target children, install handlers or introduce native waiters.
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    _child_policy()
    if threading.active_count() != 1:
        raise client.OwnedLaunchError('service must start before any foreign thread')
    _SERVICE_AUTHORITY = object()
    broker = _ServiceBroker(root, authority=_SERVICE_AUTHORITY)
    broker.token = token
    try:
        with broker:
            os.write(ready_fd, b'R')
            os.close(ready_fd)
            # Owner lifetime channel is held solely by the facade. EOF also
            # cancels targets when the controller exits without context cleanup.
            while os.read(owner_fd, 1):
                pass
    finally:
        os.close(owner_fd)
        (Path(root) / 'service-final.json').write_text(json.dumps(dict(
            receipts=broker.receipts, jobs=list(broker.jobs),
            collection_errors=broker.collection_errors, cancelled=broker.cancelled)))
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 6 or sys.argv[1] != '--service':
        raise SystemExit('expected isolated broker service descriptors')
    raise SystemExit(_service_main(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])))
