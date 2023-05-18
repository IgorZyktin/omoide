# -*- coding: utf-8 -*-
"""Repository that perform CRUD operations on EXIF.
"""
import sqlalchemy as sa
from asyncpg import exceptions

from omoide.domain import errors
from omoide.domain import models
from omoide.domain.interfaces.in_storage import in_rp_exif
from omoide.domain.special_types import Failure
from omoide.domain.special_types import Result
from omoide.domain.special_types import Success
from omoide.infra import impl
from omoide.storage import storage_models


class EXIFRepository(in_rp_exif.AbsEXIFRepository):
    """Repository that perform CRUD operations on EXIF records."""

    async def create_exif(
            self,
            user: models.User,
            exif: models.EXIF,
    ) -> Result[errors.Error, models.EXIF]:
        """Create."""
        stmt = sa.insert(
            storage_models.EXIF
        ).values(
            item_uuid=exif.item_uuid,
            exif=impl.json.dumps(exif.exif, ensure_ascii=False),
        )

        try:
            await self.db.execute(stmt)
        except exceptions.UniqueViolationError as exc:
            result = Failure(
                errors.AlreadyExist(
                    uuid=exif.item_uuid,
                    object='EXIF',
                    exception=exc,
                )
            )
        else:
            result = exif

        return result

    async def read_exif(
            self,
            uuid: impl.UUID,
    ) -> Result[errors.Error, models.EXIF]:
        """Read."""
        stmt = sa.select(
            models.EXIF
        ).where(
            models.EXIF.item_uuid == uuid
        )

        response = await self.db.fetch_one(stmt)

        if response is not None:
            result = models.EXIF(
                item_uuid=response['item_uuid'],
                exif=impl.json.loads(response['exif']),
            )
        else:
            result = Failure(
                errors.DoesNotExist(
                    uuid=uuid,
                    object='EXIF',
                )
            )

        return result

    async def update_exif(
            self,
            user: models.User,
            exif: models.EXIF,
    ) -> Result[errors.Error, models.EXIF]:
        """Update."""
        stmt = sa.update(
            storage_models.EXIF
        ).where(
            storage_models.EXIF.item_uuid == exif.item_uuid
        ).values(
            exif=impl.json.dumps(exif.exif, ensure_ascii=False),
        ).returning(1)

        response = await self.db.fetch_one(stmt)

        if response is not None:
            result = Success(exif)
        else:
            result = Failure(
                errors.DoesNotExist(
                    uuid=exif.item_uuid,
                    object='EXIF',
                )
            )

        return result

    async def delete_exif(
            self,
            item_uuid: impl.UUID,
    ) -> Result[errors.Error, impl.UUID]:
        """Delete."""
        stmt = sa.delete(
            storage_models.EXIF
        ).where(
            storage_models.EXIF.item_uuid == item_uuid
        ).returning(1)

        response = await self.db.fetch_one(stmt)

        if response is not None:
            result = Success(item_uuid)
        else:
            result = Failure(
                errors.DoesNotExist(
                    uuid=item_uuid,
                    object='EXIF',
                )
            )

        return result
