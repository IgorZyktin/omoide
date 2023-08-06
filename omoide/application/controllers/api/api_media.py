"""Media related API operations.
"""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import use_cases
from omoide import utils
from omoide.domain import interfaces
from omoide.domain.application import input_models
from omoide.domain.core import core_models
from omoide.infra.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web

router = APIRouter(prefix='/api/media')


@router.post('/{uuid}', status_code=status.HTTP_202_ACCEPTED)
async def api_create_media(
        uuid: UUID,
        in_media: input_models.InMedia,
        user: core_models.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.CreateMediaUseCase = Depends(
            dep.create_media_use_case),
):
    """Create or update media entry."""
    media = core_models.Media(
        id=-1,
        owner_uuid=user.uuid,
        item_uuid=uuid,
        created_at=utils.now(),
        processed_at=None,
        content=in_media.binary_content,
        ext=in_media.ext,
        media_type=in_media.media_type,
        replication={},
        error='',
        attempts=0,
    )

    result = await use_case.execute(policy, user, uuid, media)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {}
