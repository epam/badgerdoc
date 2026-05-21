import logging
import sys
import traceback
from datetime import timedelta
from typing import Any

from temporalio import common, workflow

from badgerdoc_common.activities import agent_log

_ACTIVITY_TIMEOUT = timedelta(seconds=10)
_NO_RETRY = common.RetryPolicy(maximum_attempts=1)


class AgentLogger:

    def __init__(
        self,
        document_id: int,
        task_id: int | None = None,
        source: str = "Temporal",
    ) -> None:
        self._document_id = document_id
        self._task_id = task_id
        self._source = source
        name = (
            f"badgerdoc_agent.{document_id}.{task_id}"
            if task_id is not None
            else f"badgerdoc_agent.{document_id}"
        )
        self.default_logger = logging.getLogger(name)

    async def _log(
        self,
        level: int,
        level_name: str,
        msg: str,
        *args: Any,
        code: str | None = None,
        markdown: str | None = None,
        document: int | None = None,
        workflow_params: dict[str, Any] | None = None,
    ) -> None:
        self.default_logger.log(level, msg, *args)

        formatted_msg = msg % args if args else msg
        log: dict[str, Any] = {"message": formatted_msg}
        if args:
            try:
                formatted_msg = msg % args
            except Exception:
                self.default_logger.exception(
                    "Unable to format agent log message"
                )
                formatted_msg = f"{msg} | args={args!r}"
        else:
            formatted_msg = msg

        if markdown is not None:
            log["markdown"] = markdown
        if code is not None:
            log["code"] = code
        if document is not None:
            log["document"] = document
        if workflow_params is not None:
            log["workflow_params"] = workflow_params

        try:
            await workflow.execute_activity(
                agent_log.write_agent_log,
                args=[
                    self._document_id,
                    self._task_id,
                    level_name,
                    self._source,
                    log,
                ],
                start_to_close_timeout=_ACTIVITY_TIMEOUT,
                retry_policy=_NO_RETRY,
            )
        except Exception:
            self.default_logger.exception("Unable to log into agent_logger")

    async def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self._log(logging.DEBUG, "DEBUG", msg, *args, **kwargs)

    async def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self._log(logging.INFO, "INFO", msg, *args, **kwargs)

    async def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self._log(logging.WARNING, "WARNING", msg, *args, **kwargs)

    async def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self._log(logging.ERROR, "ERROR", msg, *args, **kwargs)

    async def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self._log(logging.CRITICAL, "CRITICAL", msg, *args, **kwargs)

    async def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        tb = _current_traceback()
        if tb:
            existing_code = kwargs.get("code")
            kwargs["code"] = (
                f"{existing_code}\n\n{tb}" if existing_code else tb
            )
        await self._log(logging.ERROR, "ERROR", msg, *args, **kwargs)


def _current_traceback() -> str | None:
    exc_type, _, _ = sys.exc_info()
    if exc_type is None:
        return None
    return traceback.format_exc()


def get_logger(
    document_id: int,
    task_id: int | None = None,
    source: str = "Temporal",
) -> AgentLogger:
    return AgentLogger(document_id, task_id, source)
