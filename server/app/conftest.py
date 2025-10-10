import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def ensure_data_dir():
    data_dir = os.path.join(os.path.dirname(__file__), "../../data")
    abs_data_dir = os.path.abspath(data_dir)
    os.makedirs(abs_data_dir, exist_ok=True)
