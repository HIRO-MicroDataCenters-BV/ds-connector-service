import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def ensure_data_dir():
    # Get the absolute path to the project root (server directory)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
