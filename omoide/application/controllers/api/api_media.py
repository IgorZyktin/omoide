"""Media related API operations.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import use_cases
from omoide import utils
from omoide.application import web
from omoide.domain.application import input_models
from omoide.domain.core import core_models
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/media')


@router.post('/{item_uuid}', status_code=status.HTTP_201_CREATED)
async def api_create_media(
        item_uuid: UUID,
        in_media: input_models.InMedia,
        user: Annotated[core_models.User, Depends(dep.get_known_user)],
        use_case: Annotated[use_cases.CreateMediaUseCase,
                            Depends(dep.api_create_media_use_case)],
):
    """Create or update media entry."""
    media = core_models.Media(
        id=-1,
        created_at=utils.now(),
        processed_at=None,
        error='',
        owner_uuid=user.uuid,  # type: ignore
        item_uuid=item_uuid,
        media_type=in_media.media_type,
        content=in_media.get_binary_content(),
        ext=in_media.ext,
    )

    result = await web.run(use_case.execute, user, item_uuid, media)

    return {'media_id': result.id}


@router.put('/{source_uuid}/copy_image/{target_uuid}')
async def api_copy_image_from_given_item(
        source_uuid: UUID,
        target_uuid: UUID,
        user: Annotated[core_models.User, Depends(dep.get_known_user)],
        use_case: Annotated[use_cases.ApiCopyImageUseCase,
                            Depends(dep.api_item_copy_image_use_case)],
):
    """Copy image from given item."""
    await web.run(use_case.execute, user, source_uuid, target_uuid)

    return {}
