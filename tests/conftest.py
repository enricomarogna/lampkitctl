import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from lampkitctl import auth_cache


@pytest.fixture(autouse=True)
def _clear_auth_cache():
    auth_cache.clear()
