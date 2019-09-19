import pytest

from pathlib import Path


@pytest.fixture(scope='session')
def testdata():
    return Path(__file__).parent / 'data'


@pytest.fixture(scope='session')
def profile_path(testdata):
    return testdata / 'test.prf'
