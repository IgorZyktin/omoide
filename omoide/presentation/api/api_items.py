"""Item related API operations."""

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from omoide import interfaces
from omoide import models
from omoide import use_cases
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/items')


@router.put('/{uuid}/parent/{new_parent_uuid}')
async def api_item_update_parent(
    uuid: UUID,
    new_parent_uuid: UUID,
    user: models.User = Depends(dep.get_current_user),
    policy: interfaces.AbsPolicy = Depends(dep.get_policy),
    use_case: use_cases.ApiItemUpdateParentUseCase = Depends(
        dep.api_item_update_parent_use_case
    ),
):
    """Set new parent for the item."""
    result = await use_case.execute(policy, user, uuid, new_parent_uuid)
    return {'result': str(result)}
