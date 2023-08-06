"""Media related API operations.
"""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from omoide import use_cases
from omoide import utils
from omoide.domain import interfaces
from omoide.domain.application import input_models
from omoide.domain.core import core_models
from omoide.infra.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web

router = APIRouter(prefix='/api/media')


def cast_media(
        user: core_models.User,
        uuid: UUID,
        in_media: list[input_models.InMedia],
) -> list[core_models.Media]:
    """Convert media from input to domain models."""
    now = utils.now()
    return [
        core_models.Media(
            id=-1,
            owner_uuid=user.uuid,
            item_uuid=uuid,
            created_at=now,
            processed_at=None,
            content=each.binary_content,
            ext=each.ext,
            target_folder=each.target_folder,
            replication={},
            error='',
            attempts=0,
        )
        for each in in_media
    ]


@router.post('/{uuid}')
async def api_create_media(
        uuid: UUID,
        in_media: list[input_models.InMedia],
        user: core_models.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.CreateMediaUseCase = Depends(
            dep.create_media_use_case),
):
    """Create or update media entry."""
    media = cast_media(user, uuid, in_media)
    result = await use_case.execute(policy, user, uuid, media)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {}
