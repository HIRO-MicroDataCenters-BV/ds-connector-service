from pathlib import Path

import pytest

# Ensure data directory exists before any imports that might use it
# This runs at module import time, before any test collection
_data_dir = Path("./data").resolve()
_data_dir.mkdir(exist_ok=True)


@pytest.fixture(scope="session", autouse=True)
def ensure_data_dir():
    """Ensure the data directory exists for tests.

    This fixture is kept for backwards compatibility and additional
    test environment setup if needed.
    """
    # The directory is already created above, but we can add
    # additional test-specific setup here if needed
    yield _data_dir
