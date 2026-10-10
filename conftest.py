"""Tests must never read/write a developer's persisted demo snapshots."""
import os
import tempfile

_TEST_ENV = None
_PREVIOUS = {}


def pytest_sessionstart(session):
    global _TEST_ENV
    _TEST_ENV = tempfile.TemporaryDirectory(prefix='greenprint-tests-')
    for key, value in {'GREENPRINT_DB_PATH': _TEST_ENV.name + '/properties.db',
                       'GREENPRINT_PROPERTY_DATASET': 'csv', 'LLM_PROVIDER': 'deterministic'}.items():
        _PREVIOUS[key] = os.environ.get(key)
        os.environ[key] = value


def pytest_sessionfinish(session, exitstatus):
    for key, value in _PREVIOUS.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    if _TEST_ENV is not None:
        _TEST_ENV.cleanup()
