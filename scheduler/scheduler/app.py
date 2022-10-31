import asyncio
from typing import Dict, Optional

import tenant_dependency
from fastapi import Depends, FastAPI, Header, HTTPException, status
from scheduler.db import service

from scheduler import config, heartbeat, kafka_utils, log, runner, schemas

logger = log.get_logger(__name__)

tenant = tenant_dependency.get_tenant_info(
    url=config.KEYCLOAK_URI, algorithm="RS256"
)

app = FastAPI(
    title="Scheduler",
    root_path=config.ROOT_PATH,
)

NO_UNIT = "No such unit."
NO_TENANT = "User don't have permissions for tenant of the required unit."


@app.on_event("startup")
async def startup_event() -> None:
    consumer, producer = await kafka_utils.initialize_kafka()
    asyncio.create_task(heartbeat.heartbeat(producer))
    asyncio.create_task(runner.start_runner(consumer, producer))


@app.get("/unit", status_code=200, response_model=schemas.StatusOut)
async def get_status(
    unit_id: str,
    tenant_data: tenant_dependency.TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> Dict[str, str]:
    """Get Unit status from DB by unit id."""
    with service.Session() as session:
        unit = service.get_unit_by_id(session, unit_id)
    if unit is None:
        raise HTTPException(status_code=404, detail=NO_UNIT)
    if unit.tenant not in tenant_data.tenants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=NO_TENANT,
        )
    return {"status": unit.status}
