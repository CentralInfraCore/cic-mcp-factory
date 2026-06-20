import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES_DIR = pathlib.Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR
