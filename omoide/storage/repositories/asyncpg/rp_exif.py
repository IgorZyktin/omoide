"""Repository that performs CRUD operations on EXIF.
"""
from uuid import UUID

import sqlalchemy as sa

from omoide.domain import errors
from omoide.domain.core import core_models
from omoide.domain.errors import Error
from omoide.domain.storage.interfaces.in_rp_exif import AbsEXIFRepository
from omoide.infra import impl
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Result
from omoide.infra.special_types import Success
from omoide.storage.database import models as db_models  # FIXME


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
            exif=impl.json.dumps(exif.exif, ensure_ascii=False),
        )

        try:
            await self.db.execute(stmt)
        except Exception as exc:
            # TODO - which error exactly?
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
            exif=impl.json.dumps(exif.exif, ensure_ascii=False),
        )

        try:
            await self.db.execute(stmt)
        except Exception as exc:
            # TODO - which error exactly?
            result = Failure(errors.DatabaseError(exception=exc))
        else:
            result = Success(exif)

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
            # TODO - which error exactly?
            result = Failure(errors.DatabaseError(exception=exc))
        else:

            if response is not None:
                result = Success(
                    core_models.EXIF(
                        item_uuid=response['item_uuid'],
                        exif=impl.json.loads(response['exif']),
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
            # TODO - which error exactly?
            result = Failure(errors.DatabaseError(exception=exc))
        else:
            deleted = response is not None

            if deleted:
                result = Success(None)
            else:
                result = Failure(errors.EXIFDoesNotExist(item_uuid=item_uuid))

        return result
