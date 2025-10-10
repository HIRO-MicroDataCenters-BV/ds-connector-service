import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def ensure_data_dir():
    # Create the data directory in the current working directory of the test runner
    data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)
