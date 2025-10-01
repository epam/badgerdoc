import logging
from dataclasses import dataclass
from datetime import datetime

import filter_lib
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from veeva.models import orm
from veeva.models.orm import Configuration, SynchronizationLog
from veeva.services import configuration, veeva_synchronization

logger = logging.getLogger(__name__)


class SynchronzationCreationError(Exception):
    pass


class SynchronizationNotFoundError(Exception):
    pass


@dataclass
class Synchronization:
    id: int | None = None
    configuration_id: int | None = None
    status: orm.SynchronizationStatus | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def from_orm(self, orm_sync: orm.Synchronization) -> "Synchronization":
        return Synchronization(
            **{
                column.name: getattr(orm_sync, column.name)
                for column in orm_sync.__table__.columns
            }
        )

    async def create(
        self,
        session: AsyncSession,
        tenant: str,
    ) -> "Synchronization":
        # TODO, should we pass Configuration object here?
        logger.debug(
            "Creating synchronization for tenant: %s with configuration: %d",
            tenant,
            self.configuration_id,
        )

        async with session.begin():
            try:
                await configuration.Configuration(
                    id=self.configuration_id, tenant=tenant
                ).get(session)
            except configuration.ConfigurationNotFoundError:
                logger.error(
                    "Configuration with ID %d not found for tenant %s",
                    self.configuration_id,
                    tenant,
                )
                raise SynchronizationNotFoundError(
                    f"Configuration with ID {self.configuration_id} not found for tenant {tenant}"
                )

            sync_record = orm.Synchronization(
                created_by=self.created_by,
                configuration_id=self.configuration_id,
                status=self.status,
            )

            session.add(sync_record)
            await session.flush()
            await session.refresh(sync_record)
            sync_result = self.from_orm(sync_record)
        return sync_result

    async def __update_status(
        self, session: AsyncSession, status: orm.SynchronizationStatus
    ) -> None:
        update_stmt = (
            sqlalchemy.update(orm.Synchronization)
            .where((orm.Synchronization.id == self.id))
            .values(status=status)
        )

        result = await session.execute(update_stmt)
        if result.rowcount == 0:
            raise SynchronizationNotFoundError(
                f"Synchronization with ID {self.id} not found or not in pending status"
            )
        self.status = status

    async def run(self, session: AsyncSession):
        await self.__update_status(session, "in_progress")
        try:
            await veeva_synchronization.run()
        except veeva_synchronization.VeevaError:
            await self.__update_status(session, "failed")


async def __set_next_synchronization_to_progress(
    session: AsyncSession,
) -> Synchronization | None:
    """
    Get the next pending synchronization job.

    This function retrieves the next synchronization job that is in 'pending' status.

    Returns:
        Synchronization: The next pending synchronization job, or None if no pending jobs exist
    """
    async with session.begin():
        stmt = (
            sqlalchemy.select(Synchronization)
            .join(Synchronization.configuration)
            .options(
                sqlalchemy.orm.selectinload(Synchronization.configuration)
            )
            .where(
                (Synchronization.status == "pending")
                & (~Configuration.soft_deleted)
            )
            .order_by(Synchronization.created_at.asc())
            .with_for_update()
            .limit(1)
        )

        result = await session.execute(stmt)
        synchronization = result.scalars().first()

        if not synchronization:
            return None

        synchronization.status = "in_progress"
        await session.flush()
        session.expunge_all()
    return synchronization


async def run_next_pending_synchronization(
    session: AsyncSession,
) -> Synchronization:
    """
    Run the next pending synchronization job.

    This function retrieves the next pending synchronization job and marks it as running.

    Args:
        session: The async SQLAlchemy session for database operations

    Returns:
        Synchronization: The next pending synchronization job, or None if no pending jobs exist
    """
    logger.debug("Running next pending synchronization")

    # Get the next pending synchronization with FOR UPDATE lock
    synchronization = await __set_next_synchronization_to_progress(session)
    if synchronization is None:
        logger.info("No pending synchronizations to run")
        return None

    await veeva_synchronization.run(
        session=session,
        synchronization=synchronization,
    )
    return synchronization


async def run_synchronization_force(
    session: AsyncSession,
    synchronization_id: int,
) -> Synchronization:
    """
    Force run a specific synchronization job by ID.

    This function retrieves a synchronization job by its ID and runs it immediately,
    regardless of its current status.

    Args:
        session: The async SQLAlchemy session for database operations
        synchronization_id: ID of the synchronization job to run

    Returns:
        Synchronization: The updated synchronization job after running it

    Raises:
        SynchronizationNotFoundError: If the synchronization with the given ID does not exist
            or is soft deleted
    """
    logger.debug("Force running synchronization ID %d", synchronization_id)
    async with session.begin():
        # Retrieve the synchronization job by ID
        stmt = (
            sqlalchemy.select(Synchronization)
            .join(Synchronization.configuration)
            .where(Synchronization.id == synchronization_id)
            .with_for_update()
        )
        result = await session.execute(stmt)
        synchronization = result.scalar_one_or_none()

        if synchronization is None:
            raise SynchronizationNotFoundError(
                f"Synchronization with ID {synchronization_id} not found or already soft deleted"
            )

        # Set status to in_progress and run the synchronization
        synchronization.status = "in_progress"
        await session.flush()
        session.expunge(synchronization)


async def cancel_all_running_synchronizations(
    session: AsyncSession, reason: str
) -> None:
    """
    Cancel all currently running synchronization jobs.

    Args:
        session: The async SQLAlchemy session for database operations
        reason: Reason for cancellation that will be logged

    Returns:
        None
    """
    logger.warning("Cancelling all running synchronization jobs")

    async with session.begin():
        # First, get all running synchronizations to log cancellation for each
        running_stmt = (
            sqlalchemy.select(Synchronization.id)
            .where(Synchronization.status == "in_progress")
            .with_for_update()
        )
        result = await session.execute(running_stmt)
        running_ids = result.scalars().all()

        # Update all running synchronizations to cancelled
        update_stmt = (
            sqlalchemy.update(Synchronization)
            .where(Synchronization.status == "in_progress")
            .values(status="cancelled")
        )
        update_result = await session.execute(update_stmt)

        # Add log entry for each cancelled synchronization
        for sync_id in running_ids:
            log_message = f"Synchronization cancelled: {reason}"
            await add_log_string(session, sync_id, log_message)

        logger.info(
            "Cancelled all running synchronization jobs, affected rows: %d",
            (
                update_result.rowcount
                if hasattr(update_result, "rowcount")
                else "unknown"
            ),
        )


async def add_log_string(
    session: AsyncSession, synchronization_id: int, log_string: str
) -> None:
    """
    Add a log string to the synchronization job.

    Args:
        session: The async SQLAlchemy session for database operations
        synchronization_id: ID of the synchronization job
        log_string: Log message to be added

    Returns:
        None
    """
    logger.debug(
        "Adding log string to synchronization ID %d", synchronization_id
    )
    session.add(
        SynchronizationLog(
            synchronization_id=synchronization_id,
            message=log_string,
        )
    )

    await session.commit()
    logger.info(
        "Log string added to synchronization ID %d", synchronization_id
    )


async def get_by_id(
    session: AsyncSession,
    synchronization_id: int,
    tenant: str,
) -> Synchronization:
    """
    Retrieve a synchronization job by its ID.

    Args:
        session: The async SQLAlchemy session for database operations
        synchronization_id: ID of the synchronization job to retrieve
        tenant: Tenant identifier for multi-tenancy support

    Returns:
        Synchronization: The retrieved synchronization job

    Raises:
        SynchronizationNotFoundError: If the synchronization with the given ID does not exist
            or is soft deleted
    """
    logger.info(
        "Retrieving synchronization ID %d for tenant %s",
        synchronization_id,
        tenant,
    )

    stmt = (
        sqlalchemy.select(Synchronization)
        .join(Synchronization.configuration)
        .where(
            (Synchronization.id == synchronization_id)
            & (Configuration.tenant == tenant)
        )
    )

    result = await session.execute(stmt)
    sync = result.scalar_one_or_none()

    if sync is None:
        raise SynchronizationNotFoundError(
            f"Synchronization with ID {synchronization_id} not found or already soft deleted"
        )

    return Synchronization(
        id=sync.id,
        configuration_id=sync.configuration_id,
        status=sync.status,
        created_by=sync.created_by,
        created_at=sync.created_at,
        updated_at=sync.updated_at,
    )


async def get_all_query(
    session: sqlalchemy.orm.Session,  # todo: change to AsyncSession when filter_lib supports it
    tenant: str,
    filters: dict,
) -> tuple[sqlalchemy.Select, filter_lib.PaginationParams]:
    """
    Get all synchronizations with optional filtering.

    Args:
        session: The async SQLAlchemy session for database operations
        tenant: Tenant identifier for multi-tenancy support
        filters: Dictionary of filters to apply to the query

    Returns:
        tuple: A tuple containing the SQLAlchemy Select object and pagination details
    """
    logger.debug(
        "Getting all synchronizations for tenant %s with filters %s",
        tenant,
        filters,
    )

    filter_args = filter_lib.map_request_to_filter(filters, "Synchronization")
    query = session.query(Synchronization)
    print(session)
    query, pag = filter_lib.form_query(filter_args, query)
    return query, pag
