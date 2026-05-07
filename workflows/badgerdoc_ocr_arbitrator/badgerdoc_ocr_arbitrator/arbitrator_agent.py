import logging
import os
import re
from importlib import import_module
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field

from badgerdoc_common import badgerdoc_event


logger = logging.getLogger(__name__)


ARBITRATOR_AGENT_INSTRUCTIONS = (
    "You are given user prompt."
    "It might contain tasks, engines and objects."
    "Your goal is to understand which engine or engines user is interested to run and return corresponding ids."
    "To get engine-to-id mapping you must call mapping_tool first."
    "Use mapping_tool output to select the closest engine or engines from keys and return matching ids."
)


class WorkflowSelectionOutput(BaseModel):
    workflow_ids: list[int] = Field(default_factory=list)


@dataclass
class ArbitratorAgent:
    """Small pydantic-based agent to selects workflows."""

    def _build_agent(self, tools: list[Callable]) -> Any:
        logger.debug("Building pydantic_ai arbitrator agent")
        pydantic_ai_module = import_module("pydantic_ai")
        Agent = pydantic_ai_module.Agent
        openai_model_cls = import_module("pydantic_ai.models.openai").OpenAIModel
        openai_provider_cls = import_module("pydantic_ai.providers.openai").OpenAIProvider
        from openai import AsyncAzureOpenAI  # pylint: disable=import-outside-toplevel

        openai_client = AsyncAzureOpenAI(
            api_key=os.environ.get("ARBITRATOR_API_KEY"),
            azure_endpoint="https://ai-proxy.lab.epam.com",
            api_version="2024-02-01",
        )
        model = openai_model_cls(
            os.environ.get("ARBITRATOR_MODEL"),
            provider=openai_provider_cls(openai_client=openai_client),
        )

        agent = Agent(
            model,
            output_type=WorkflowSelectionOutput,
            tools=tools,
            instructions=ARBITRATOR_AGENT_INSTRUCTIONS,
        )

        return agent


    async def get_target_workflows(
        self,
        llm_params: str,
        mapping_tool: Callable
    ) -> list[int | None]:
        logger.info(
            "Get target workflow ids for prompt=%s", llm_params
        )
        try:
            logger.info("Starts LLM-based workflow selection")
            agent = self._build_agent(tools=[mapping_tool])
            result = await agent.run(
                (
                    "user_prompt:\n"
                    f"{llm_params}\n\n"
                    "Select workflow ids to trigger."
                ),
            )
            selected_ids = set(result.output.workflow_ids)
            if selected_ids:
                logger.info(
                    "LLM selected workflow IDs: %s",
                    sorted(selected_ids),
                )
                return selected_ids
            logger.info("LLM selection returned no workflow IDs")
            return []
        except Exception:
            logger.exception(
                "LLM workflow selection failed"
            )
