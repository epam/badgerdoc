import logging
import os
from asyncio import Task, create_task, sleep

from fastapi import FastAPI

from veeva.core.db import LOCAL_SESSION
from veeva.routes import configurations
from veeva.services import synchronization
from veeva.veeva.routes import synchronizations

ROOT_PATH = os.getenv("ROOT_PATH", "/veeva")

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG").upper())

app = FastAPI(
    title="BadgerDoc Veeva PM Synchronization Service",
    description="A microservice that synchronizes Veeva Promomats with BadgerDoc",
    version=open("version.txt").read().strip(),
    root_path=ROOT_PATH,
)

# Store the background task so we can cancel it on shutdown
background_tasks: list[Task] = []


async def synchronization_worker():
    """Background worker that periodically checks for pending synchronizations"""
    logger.info("Synchronization worker started")
    try:
        while True:
            pending_syncs = await synchronization.run_next_pending_synchronization(
                LOCAL_SESSION()
            )
            logger.info("Synchronization worker cycle completed")
            await sleep(60)
    except Exception as e:
        logger.error(f"Synchronization worker encountered an error: {e}")
    finally:
        logger.info("Synchronization worker stopped")


@app.on_event("startup")
async def startup_event():
    """Initialize background tasks when the application starts"""
    logger.info("Starting background synchronization workers")
    task = create_task(synchronization_worker())
    background_tasks.append(task)


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up background tasks when the application shuts down"""
    logger.info("Stopping background synchronization workers")
    for task in background_tasks:
        if not task.done():
            task.cancel()

    await synchronization.cancel_all_running_synchronizations(
        LOCAL_SESSION(), "Stopping all synchronizations on shutdown"
    )


app.include_router(configurations.router)
app.include_router(synchronizations.router)
