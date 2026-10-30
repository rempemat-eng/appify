"""Exact unittest classes, failfast observations and retained first errors."""
import json
from pathlib import Path
import sys
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
    result = unittest.TextTestRunner(verbosity=2, failfast=True, resultclass=Result).run(suite)
finally:
    destination.write_text(json.dumps(observed, indent=2) + '\n')
raise SystemExit(0 if result.wasSuccessful() else 1)
