"""Repository that performs CRUD operations on EXIF.
"""
from uuid import UUID

import sqlalchemy as sa
from asyncpg import exceptions

from omoide.domain import errors
from omoide.domain.core import core_models
from omoide.domain.errors import Error
from omoide.domain.storage.interfaces.in_rp_exif import AbsEXIFRepository
from omoide.infra import custom_logging
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.storage.database import db_models

LOG = custom_logging.get_logger(__name__)


class EXIFRepository(AbsEXIFRepository):
    """Repository that performs CRUD operations on EXIF."""

    async def create_exif(
            self,
            exif: core_models.EXIF,
    ) -> Result[errors.Error, core_models.EXIF]:
        """Create EXIF."""
        stmt = sa.insert(
            db_models.EXIF
        ).values(
            item_uuid=exif.item_uuid,
            exif=exif.exif,
        )

        try:
            await self.db.execute(stmt)
        except exceptions.UniqueViolationError:
            result = Failure(errors.EXIFAlreadyExist(item_uuid=exif.item_uuid))
        except Exception as exc:
            LOG.exception('Failed to create exif')  # TODO - refactor
            result = Failure(errors.DatabaseError(exception=exc))
        else:
            result = Success(exif)

        return result

    async def update_exif(
            self,
            exif: core_models.EXIF,
    ) -> Result[Error, core_models.EXIF]:
        """Update EXIF."""
        stmt = sa.update(
            db_models.EXIF
        ).where(
            db_models.EXIF.item_uuid == exif.item_uuid
        ).values(
            exif=exif.exif,
        ).returning(1)

        try:
            response = await self.db.fetch_one(stmt)
        except Exception as exc:
            LOG.exception('Failed to update exif')  # TODO - refactor
            result = Failure(errors.DatabaseError(exception=exc))
        else:
            updated = response is not None

            if updated:
                result = Success(exif)
            else:
                result = Failure(
                    errors.EXIFDoesNotExist(item_uuid=exif.item_uuid),
                )

        return result

    async def get_exif_by_item_uuid(
            self,
            item_uuid: UUID,
    ) -> Result[errors.Error, core_models.EXIF]:
        """Return EXIF."""
        stmt = sa.select(
            db_models.EXIF
        ).where(
            db_models.EXIF.item_uuid == item_uuid
        )

        try:
            response = await self.db.fetch_one(stmt)
        except Exception as exc:
            LOG.exception('Failed to get exif')  # TODO - refactor
            result = Failure(errors.DatabaseError(exception=exc))
        else:

            if response is not None:
                result = Success(
                    core_models.EXIF(
                        item_uuid=response['item_uuid'],
                        exif=response['exif'],
                    )
                )
            else:
                result = Failure(errors.EXIFDoesNotExist(item_uuid=item_uuid))

        return result

    async def delete_exif(
            self,
            item_uuid: UUID,
    ) -> Result[errors.Error, None]:
        """Delete EXIF."""
        stmt = sa.delete(
            db_models.EXIF
        ).where(
            db_models.EXIF.item_uuid == item_uuid
        ).returning(1)

        try:
            response = await self.db.fetch_one(stmt)
        except Exception as exc:
            LOG.exception('Failed to delete exif')  # TODO - refactor
            result = Failure(errors.DatabaseError(exception=exc))
        else:
            deleted = response is not None

            if deleted:
                result = Success(None)
            else:
                result = Failure(errors.EXIFDoesNotExist(item_uuid=item_uuid))

        return result
