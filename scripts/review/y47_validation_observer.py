"""Exact unittest classes, failfast observations and retained first errors."""
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import traceback
import unittest

source, selector, destination = sys.argv[1:]
destination = Path(destination)
sys.path.insert(0, source)
observed = []

def capture_first(error, root=None):
    target = destination.with_name(destination.stem + '-first-error.txt')
    if not target.exists():
        target.write_text(''.join(traceback.format_exception(*error)))
    if root is not None and Path(root).is_dir():
        for i, log in enumerate(sorted(Path(root).rglob('service.log'))):
            if log.is_file() and not log.is_symlink():
                copied = destination.with_name(destination.stem + '-inner-' + str(i) + '.log')
                if not copied.exists():
                    copied.write_bytes(log.read_bytes()[:1024 ** 2])

def capture_adapter_exit(error, name):
    """Retain owned method-local logs before TemporaryDirectory removes them."""
    report = dict(root=str(name), status='FAILED', files=[], errors=[])
    try:
        capture_first(error)
        temporary = Path(os.environ['TMPDIR'])
        root = Path(name)
        prefixes = ('owned-git-', 'owned-command-', 'owned-tool-routing-',
                    'owned-timeout-', 'owned-engine-log-', 'owned-refusal-')
        if (not temporary.is_absolute() or temporary.resolve() != destination.parent.parent / 't'
                or not root.is_absolute() or root.is_symlink() or root.resolve() != root
                or root.parent != temporary.resolve() or not root.name.startswith(prefixes)):
            raise ValueError('refuse evidence outside owned receiving TMPDIR adapter root')
        if not root.is_dir():
            raise FileNotFoundError('owned adapter root missing before context cleanup')
        remaining, visited, attempted = 4 * 1024 ** 2, 0, 0
        for folder, directories, files in os.walk(root, followlinks=False,
                onerror=lambda error: report['errors'].append(dict(path=error.filename, error=repr(error)))):
            visited += 1 + len(directories) + len(files)
            if visited > 256:
                raise ValueError('adapter evidence traversal exceeds 256 entries')
            directories[:] = sorted(d for d in directories if not (Path(folder) / d).is_symlink())
            for filename in sorted(files):
                if not (filename.endswith('.log') or filename in ('stdout.txt', 'stderr.txt')):
                    continue
                if attempted >= 16 or remaining <= 0:
                    raise ValueError('adapter evidence exceeds 16 files or 4MiB')
                log = Path(folder) / filename
                try:
                    if log.resolve().parent != Path(folder) or log.is_symlink():
                        raise ValueError('refuse symlink evidence path')
                    fd = os.open(log, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                    with os.fdopen(fd, 'rb') as stream:
                        info = os.fstat(stream.fileno())
                        if not stat.S_ISREG(info.st_mode):
                            raise ValueError('refuse non-regular evidence file')
                        data = stream.read(min(1024 ** 2, remaining))
                    copied = destination.with_name(destination.stem + '-adapter-' + str(attempted) + '.log')
                    attempted += 1
                    remaining -= len(data)
                    with copied.open('xb') as output:
                        output.write(data)
                    report['files'].append(dict(source=str(log.relative_to(root)),
                        retained=copied.name, source_bytes=info.st_size, retained_bytes=len(data),
                        truncated=info.st_size > len(data)))
                except Exception:
                    report['errors'].append(dict(source=str(log.relative_to(root)),
                        traceback=traceback.format_exc()))
        report['status'] = 'PARTIAL' if report['errors'] or any(f['truncated'] for f in report['files']) else 'RETAINED'
    except BaseException:
        report['errors'].append(dict(traceback=traceback.format_exc()))
    finally:
        # Separate extraction errors never replace the original test traceback.
        destination.with_name(destination.stem + '-adapter-retention.json').write_text(json.dumps(report, indent=2) + '\n')

original_temp_exit = tempfile.TemporaryDirectory.__exit__

def adapter_temp_exit(self, exc_type, exc_value, exc_traceback):
    if exc_type is not None:
        try:
            capture_adapter_exit((exc_type, exc_value, exc_traceback), self.name)
        except BaseException:
            print('Y47 ADAPTER EVIDENCE EXTRACTION FAILED; original exception continues', file=sys.stderr)
            traceback.print_exc()
    # Delegate the actual cleanup, return value and any cleanup error unchanged.
    return original_temp_exit(self, exc_type, exc_value, exc_traceback)

if selector == 'service_canary':
    from scripts.review.owned_broker import Broker
    root = destination.parent / 'service-canary'
    details, code = {'state': 'STARTING', 'root': str(root)}, 1
    try:
        with Broker(root) as broker:
            details['service_pid'] = broker.service_pid
            assert broker.jobs == [] and broker.receipts == []
        details.update(state='PASSED', final_snapshot=broker.final_snapshot)
        observed.append(['service_canary', 'ok'])
        code = 0
    except BaseException:
        capture_first(sys.exc_info(), root)
        traceback.print_exc()
        details['state'] = 'FAILED'
        observed.append(['service_canary', 'ERROR'])
    finally:
        destination.with_name('canary-details.json').write_text(json.dumps(details, indent=2) + '\n')
        destination.write_text(json.dumps(observed, indent=2) + '\n')
    raise SystemExit(code)

class Result(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        observed.append([test.id(), 'ok'])
    def addFailure(self, test, error):
        capture_first(error, getattr(test, 'root', None))
        super().addFailure(test, error)
        observed.append([test.id(), 'FAIL'])
    def addError(self, test, error):
        capture_first(error, getattr(test, 'root', None))
        super().addError(test, error)
        observed.append([test.id(), 'ERROR'])
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        observed.append([test.id(), 'SKIP: ' + reason])
suite = unittest.defaultTestLoader.loadTestsFromName(selector)
try:
    if selector == 'scripts.review.test_pr_sheet.OwnedAdapterControls':
        tempfile.TemporaryDirectory.__exit__ = adapter_temp_exit
    result = unittest.TextTestRunner(verbosity=2, failfast=True, resultclass=Result).run(suite)
finally:
    tempfile.TemporaryDirectory.__exit__ = original_temp_exit
    destination.write_text(json.dumps(observed, indent=2) + '\n')
raise SystemExit(0 if result.wasSuccessful() else 1)
