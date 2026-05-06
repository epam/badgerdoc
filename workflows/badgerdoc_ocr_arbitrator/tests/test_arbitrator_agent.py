import os
import sys
from pathlib import Path

import pytest

WORKFLOWS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKFLOWS_ROOT / "badgerdoc_common"))
sys.path.insert(0, str(WORKFLOWS_ROOT / "badgerdoc_ocr_arbitrator"))

os.environ.setdefault("BADGERDOC_REST_API_RETRY_POLICY", "1,2.0,30,3")
os.environ.setdefault("TEMPORAL_BADGERDOC_ADDRESS", "http://test:8000")
os.environ.setdefault("BADGERDOC_TOKEN", "test_token")
os.environ.setdefault("TEMPORAL_ADDRESS", "localhost:7233")
os.environ.setdefault("BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT", "5")

from badgerdoc_common.badgerdoc_event import BadgerdocWorkflow
from badgerdoc_ocr_arbitrator.arbitrator_agent import (
    ArbitratorAgent,
    ParsedArbitratorPrompt,
)


def _workflow(
    workflow_id: int,
    name: str,
    tags: list[str] | None = None,
) -> BadgerdocWorkflow:
    return BadgerdocWorkflow(
        id=workflow_id,
        name=name,
        tags=tags,
        created_by=1,
        event_entity="document",
        event_type="manual_trigger",
        document_types=["pdf"],
        entity_tags=[],
        temporal_workflow_type="ocr.workflow",
        temporal_queue="ocr",
        is_active=True,
        trigger="manual",
        extraction_scope=["document"],
        support_prompts=True,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )


def test_parse_llm_params_engine_name_disables_trigger_all():
    agent = ArbitratorAgent()

    parsed = agent.parse_llm_params(
        "Please run deepseek and paddle OCR engines", user_id=None
    )

    assert parsed.trigger_all is False
    assert parsed.workflow_ids == []
    assert parsed.workflow_names == []


def test_parse_llm_params_link_only_keeps_trigger_all():
    agent = ArbitratorAgent()

    parsed = agent.parse_llm_params(
        "{{/badgerdoc/document/1/page/6/}}", user_id=None
    )

    assert parsed.trigger_all is True


def test_parse_llm_params_typo_engine_with_link_disables_trigger_all():
    agent = ArbitratorAgent()

    parsed = agent.parse_llm_params(
        "deeseek ocr {{/badgerdoc/document/1/page/6/}}",
        user_id=None,
    )

    assert parsed.trigger_all is False


def test_select_workflows_by_explicit_tag():
    agent = ArbitratorAgent()
    parsed_prompt = ParsedArbitratorPrompt(
        workflow_ids=[],
        workflow_names=[],
        prompt_text="run deepseek-ocr-2 for this document",
        trigger_all=False,
    )

    workflows = [
        _workflow(14, "DeepSeek OCR", tags=["ai-inference", "deepseek-ocr-2"]),
        _workflow(15, "Paddle OCR", tags=["ai-inference", "paddle-ocr"]),
        _workflow(21, "MinerU OCR", tags=["ai-inference", "mineru-ocr"]),
    ]

    selected = agent.select_workflows(parsed_prompt, workflows)

    assert [item.id for item in selected] == [14]


def test_build_engine_workflow_id_map_uses_env_overrides(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        "ARBITRATOR_ENGINE_WORKFLOW_IDS",
        '{"deepseek-ocr-2": 99}',
    )
    agent = ArbitratorAgent()

    workflows = [
        _workflow(14, "DeepSeek OCR", tags=["ai-inference", "deepseek-ocr-2"]),
        _workflow(15, "Paddle OCR", tags=["ai-inference", "paddle-ocr"]),
    ]

    mapping = agent._build_engine_workflow_id_map(workflows)

    assert mapping["deepseek-ocr-2"] == 99
    assert mapping["paddle-ocr"] == 15
