"""Item related API operations."""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from omoide import interfaces
from omoide import models
from omoide import use_cases
from omoide.infra.special_types import Failure
from omoide.presentation import api_models
from omoide.presentation import dependencies as dep
from omoide.presentation import web

router = APIRouter(prefix='/api/items')


@router.patch('/{uuid}')
async def api_partial_update_item(
        uuid: UUID,
        operations: list[api_models.PatchOperation],
        user: models.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemUpdateUseCase = Depends(
            dep.api_item_update_use_case),
):
    """Update item."""
    result = await use_case.execute(policy, user, uuid, operations)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}


# Not actually REST api endpoints >> heavy operations


@router.put('/{uuid}/tags')
async def api_item_update_tags(
        uuid: UUID,
        new_tags: api_models.NewTagsIn,
        user: models.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemUpdateTagsUseCase = Depends(
            dep.api_item_update_tags_use_case),
):
    """Set new tags for the item + all children."""
    result = await use_case.execute(policy, user, uuid, new_tags.tags)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}


@router.put('/{uuid}/permissions')
async def api_item_update_permissions(
        uuid: UUID,
        new_permissions: api_models.NewPermissionsIn,
        user: models.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemUpdatePermissionsUseCase = Depends(
            dep.api_item_update_permissions_use_case),
):
    """Set new permissions for the item and possibly parents/children."""
    result = await use_case.execute(policy, user, uuid, new_permissions)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}


@router.put('/{uuid}/parent/{new_parent_uuid}')
async def api_item_update_parent(
        uuid: UUID,
        new_parent_uuid: UUID,
        user: models.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemUpdateParentUseCase = Depends(
            dep.api_item_update_parent_use_case),
):
    """Set new parent for the item."""
    result = await use_case.execute(policy, user, uuid, new_parent_uuid)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}
