import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

WORKFLOWS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKFLOWS_ROOT / "badgerdoc_common"))
sys.path.insert(0, str(WORKFLOWS_ROOT / "badgerdoc_ocr_arbitrator"))

os.environ.setdefault("BADGERDOC_REST_API_RETRY_POLICY", "1,2.0,30,3")
os.environ.setdefault("TEMPORAL_BADGERDOC_ADDRESS", "http://test:8000")
os.environ.setdefault("BADGERDOC_TOKEN", "test_token")
os.environ.setdefault("TEMPORAL_ADDRESS", "localhost:7233")
os.environ.setdefault("BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT", "5")

from badgerdoc_ocr_arbitrator.arbitrator_agent import (
    ArbitratorAgent,
    WorkflowSelectionOutput,
)


def _make_mock_agent(workflow_ids: list[int]) -> MagicMock:
    """Return a mock pydantic_ai agent that resolves with the given workflow IDs."""
    mock_result = MagicMock()
    mock_result.output = WorkflowSelectionOutput(workflow_ids=workflow_ids)
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock(return_value=mock_result)
    return mock_agent


@pytest.mark.anyio
async def test_get_target_workflows_returns_selected_ids():
    agent = ArbitratorAgent()
    mapping_tool = MagicMock()

    with patch.object(
        agent, "_build_agent", return_value=_make_mock_agent([14, 15])
    ):
        result = await agent.get_target_workflows(
            "Run deepseek and paddle OCR", mapping_tool
        )

    assert set(result) == {14, 15}


@pytest.mark.anyio
async def test_get_target_workflows_returns_empty_list_when_no_ids():
    agent = ArbitratorAgent()
    mapping_tool = MagicMock()

    with patch.object(
        agent, "_build_agent", return_value=_make_mock_agent([])
    ):
        result = await agent.get_target_workflows(
            "{{/badgerdoc/document/1/page/6/}}", mapping_tool
        )

    assert result == []


@pytest.mark.anyio
async def test_get_target_workflows_returns_none_on_exception():
    agent = ArbitratorAgent()
    mapping_tool = MagicMock()

    mock_agent = MagicMock()
    mock_agent.run = AsyncMock(side_effect=RuntimeError("LLM unavailable"))

    with patch.object(agent, "_build_agent", return_value=mock_agent):
        result = await agent.get_target_workflows(
            "Run deepseek OCR", mapping_tool
        )

    assert result is None


@pytest.mark.anyio
async def test_get_target_workflows_passes_mapping_tool_to_build_agent():
    agent = ArbitratorAgent()
    mapping_tool = MagicMock()

    with patch.object(
        agent, "_build_agent", return_value=_make_mock_agent([])
    ) as mock_build:
        await agent.get_target_workflows("some prompt", mapping_tool)

    mock_build.assert_called_once_with(tools=[mapping_tool])
