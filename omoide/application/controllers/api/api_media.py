"""Media related API operations."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from omoide import models
from omoide import use_cases
from omoide.application import web
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/media')


@router.put('/{source_uuid}/copy_image/{target_uuid}')
async def api_copy_image_from_given_item(
    source_uuid: UUID,
    target_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    use_case: Annotated[use_cases.ApiCopyImageUseCase,
                        Depends(dep.api_item_copy_image_use_case)],
):
    """Copy image from given item."""
    await web.run(use_case.execute, user, source_uuid, target_uuid)
    return {}
