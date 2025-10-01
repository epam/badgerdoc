import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_session():
    session = AsyncMock()
    return session
