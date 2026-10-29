"""Optional Y12 launch client and trusted pre-exec gate (Linux only).

Source preparation: runtime controls require a separate lead allocation.
Only launches explicitly sent to the broker are accounted for. Native forks,
their memory and an independently launched top-level producer are not covered.
"""
from __future__ import annotations

import base64
import json
import math
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import uuid

SOCKET_ENV = 'MYGAME_OWNED_SOCKET'
TOKEN_ENV = 'MYGAME_OWNED_TOKEN'
PARENT_ENV = 'MYGAME_OWNED_PARENT'
MAX_REQUEST = 512 * 1024
MAX_OUTPUT = 4 * 1024 * 1024
MAX_REPLY = 2 * MAX_OUTPUT + 1024 * 1024
MAX_TIMEOUT = 3600


class OwnedLaunchError(OSError):
    """Requested managed execution failed closed; never use a local fallback."""


def requested(env=None) -> bool:
    source = os.environ if env is None else env
    return SOCKET_ENV in source or TOKEN_ENV in source or PARENT_ENV in source


def _receive(sock, limit):
    def exact(size):
        result = bytearray()
        while len(result) < size:
            chunk = sock.recv(min(65536, size - len(result)))
            if not chunk:
                raise OwnedLaunchError('owned broker channel closed before a complete reply')
            result.extend(chunk)
        return bytes(result)
    size = struct.unpack('!I', exact(4))[0]
    if size > limit:
        raise OwnedLaunchError('owned channel message exceeds its bound')
    value = json.loads(exact(size))
    if not isinstance(value, dict):
        raise OwnedLaunchError('owned channel requires an object')
    return value


def _send(sock, value, limit):
    data = json.dumps(value, separators=(',', ':'), allow_nan=False).encode()
    if len(data) > limit:
        raise OwnedLaunchError('owned channel message exceeds its bound')
    sock.sendall(struct.pack('!I', len(data)) + data)


def _request(value, env, timeout):
    path, token = env.get(SOCKET_ENV), env.get(TOKEN_ENV)
    if not path or not token or not os.path.isabs(path):
        raise OwnedLaunchError('owned mode requires an absolute broker socket and token')
    value = dict(value, token=token)
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout + 10)
            sock.connect(path)
            _send(sock, value, MAX_REQUEST)
            reply = _receive(sock, MAX_REPLY)
    except (OSError, ValueError, TypeError) as exc:
        raise OwnedLaunchError(f'owned broker request failed: {exc}') from exc
    if reply.get('error'):
        raise OwnedLaunchError(str(reply['error']))
    return reply


def cancel(env=None):
    """Close this broker allocation to further launches and cancel registered jobs."""
    return _request({'op': 'cancel'}, dict(os.environ if env is None else env), 5)


def run(args, *, cwd=None, env=None, capture_output=True, timeout=900,
        text=False, encoding=None, errors=None, check=False):
    """The explicitly supported capture-only subprocess.run subset; no local Popen."""
    environment = dict(os.environ if env is None else env)
    if not capture_output:
        raise OwnedLaunchError('owned mode requires bounded captured stdout/stderr')
    if not isinstance(args, (list, tuple)) or not args or any(not isinstance(a, str) or '\x00' in a for a in args):
        raise OwnedLaunchError('owned argv must be a nonempty string vector')
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= MAX_TIMEOUT:
        raise OwnedLaunchError('owned timeout is out of bounds')
    reply = _request(dict(op='launch', request_id=uuid.uuid4().hex,
                          parent=environment.get(PARENT_ENV, ''), args=list(args),
                          cwd=str(Path.cwd() if cwd is None else Path(cwd).resolve()),
                          env=environment, timeout=timeout), environment, timeout)
    receipt = reply.get('receipt', {})
    if receipt.get('pidfd_registered') is not True or receipt.get('waited') is not True:
        raise OwnedLaunchError('broker omitted identity registration or actual wait evidence')
    try:
        stdout = base64.b64decode(reply['stdout'], validate=True)
        stderr = base64.b64decode(reply['stderr'], validate=True)
        code = reply['returncode']
        if type(code) is not int or len(stdout) + len(stderr) > MAX_OUTPUT:
            raise ValueError('invalid result bounds/status')
    except (KeyError, ValueError, TypeError) as exc:
        raise OwnedLaunchError('malformed broker result') from exc
    if reply.get('timed_out'):
        raise subprocess.TimeoutExpired(args, timeout, output=stdout, stderr=stderr)
    if text or encoding is not None:
        stdout = stdout.decode(encoding or 'utf-8', errors or 'strict')
        stderr = stderr.decode(encoding or 'utf-8', errors or 'strict')
    result = subprocess.CompletedProcess(args, code, stdout, stderr)
    result.owned_receipt = receipt
    if check:
        result.check_returncode()
    return result


def _gate(gate_fd, spec_fd):
    """Trusted child: target code is unreachable until the parent releases the gate."""
    try:
        with os.fdopen(spec_fd, 'rb') as source:
            spec = json.loads(source.read(MAX_REQUEST + 1))
        with os.fdopen(gate_fd, 'rb', buffering=0) as gate:
            if gate.read(1) != b'1':
                return 125
        # No shell, PID discovery, signals or target imports in this helper.
        os.execvpe(spec['args'][0], spec['args'], spec['env'])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'owned target exec failed: {exc}', file=sys.stderr)
        return 127


def _module(tool_root, subject_root, module, arguments):
    """Bind subject data before reviewed detector modules capture core.REPO.

    This target bootstrap runs only after the broker's exec gate. It imports
    reviewed code, never Python modules from the subject working directory.
    """
    import importlib
    import runpy

    if module not in ('scripts.review.assets', 'scripts.review.run'):
        raise OwnedLaunchError('unsupported reviewed producer module')
    tools, subject = Path(tool_root).resolve(), Path(subject_root).resolve()
    if (not Path(tool_root).is_absolute() or not Path(subject_root).is_absolute()
            or tools != Path(__file__).resolve().parents[2]
            or not subject.is_dir() or Path.cwd().resolve() != subject):
        raise OwnedLaunchError('reviewed producer roots/cwd do not match')
    sys.path.insert(0, str(tools))
    core = importlib.import_module('scripts.review.core')
    if Path(core.__file__).resolve() != tools / 'scripts/review/core.py':
        raise OwnedLaunchError('review core did not load from the reviewed tool root')
    core.REPO = str(subject)
    # assets/run and their scene/construct/scale imports now capture subject REPO.
    sys.argv = [module, *arguments]
    runpy.run_module(module, run_name='__main__')


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--gate':
        raise SystemExit(_gate(int(sys.argv[2]), int(sys.argv[3])))
    if len(sys.argv) >= 5 and sys.argv[1] == '--module':
        _module(*sys.argv[2:5], sys.argv[5:])
    else:
        raise SystemExit('expected trusted gate descriptors or reviewed producer roots/module')
