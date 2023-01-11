# -*- coding: utf-8 -*-
"""Item related API operations.
"""
import http
import urllib.parse
from typing import Type
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from starlette.responses import PlainTextResponse

from omoide import domain
from omoide import use_cases
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.presentation import api_models
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = APIRouter(prefix='/api/items')


@router.post(
    '',
    status_code=http.HTTPStatus.CREATED,
    response_model=api_models.OnlyUUID,
)
async def api_create_item(
        request: Request,
        response: Response,
        payload: api_models.CreateItemIn,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemCreateUseCase = Depends(
            dep.api_item_create_use_case),
        templates: web.TemplateEngine = Depends(dep.get_templates),
):
    """Create item."""
    result = await use_case.execute(policy, user, payload)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    response.headers['Location'] = templates.url_for(
        request, 'api_read_item', uuid=result.value)

    return api_models.OnlyUUID(uuid=result.value)


@router.post(
    '/bulk',
    status_code=http.HTTPStatus.OK,
    response_model=list[api_models.OnlyUUID],
)
async def api_create_item_bulk(
        payload: api_models.CreateItemsIn,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemCreateBulkUseCase = Depends(
            dep.api_item_create_bulk_use_case),
):
    """Create many items at once."""
    result = await use_case.execute(policy, user, payload)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return [
        api_models.OnlyUUID(uuid=uuid)
        for uuid in result.value
    ]


@router.get('/{uuid}')
async def api_read_item(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemReadUseCase = Depends(
            dep.api_item_read_use_case),
):
    """Get item."""
    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return result.value


@router.patch('/{uuid}')
async def api_partial_update_item(
        uuid: UUID,
        operations: list[api_models.PatchOperation],
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemUpdateUseCase = Depends(
            dep.api_item_update_use_case),
):
    """Update item."""
    result = await use_case.execute(policy, user, uuid, operations)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}


@router.delete(
    '/{uuid}',
    response_model=api_models.OnlyUUID,
)
async def api_delete_item(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemDeleteUseCase = Depends(
            dep.api_item_delete_use_case),
):
    """Delete item.

    If item does not exist return 404.

    If item was successfully deleted, return UUID of the parent
    (so you could browse which items are still exist in this collection).
    """
    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return api_models.OnlyUUID(uuid=result.value)


# Not actually REST api endpoints >> heavy operations


@router.put('/{uuid}/tags')
async def api_item_update_tags(
        uuid: UUID,
        new_tags: api_models.NewTagsIn,
        user: domain.User = Depends(dep.get_current_user),
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
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemUpdatePermissionsUseCase = Depends(
            dep.api_item_update_permissions_use_case),
):
    """Set new permissions for the item and possibly parents/children."""
    result = await use_case.execute(policy, user, uuid, new_permissions)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}


@router.put('/{source_uuid}/copy_thumbnail/{target_uuid}')
async def api_copy_thumbnail_from_given_item(
        source_uuid: UUID,
        target_uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiCopyThumbnailUseCase = Depends(
            dep.api_item_copy_thumbnail_use_case),
):
    """Copy thumbnail from given item."""
    result = await use_case.execute(policy, user, source_uuid, target_uuid)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}


@router.put('/{uuid}/parent/{new_parent_uuid}')
async def api_item_update_parent(
        uuid: UUID,
        new_parent_uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemUpdateParentUseCase = Depends(
            dep.api_item_update_parent_use_case),
):
    """Set new parent for the item."""
    result = await use_case.execute(policy, user, uuid, new_parent_uuid)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}


@router.get('/download/{uuid}')
async def api_items_download(
        request: Request,
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemsDownloadUseCase = Depends(
            dep.api_items_download_use_case),
        config: Config = Depends(dep.get_config),
        templates: web.TemplateEngine = Depends(dep.get_templates),
        response_class: Type[Response] = PlainTextResponse,
):
    """Return all children as zip archive."""
    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        return web.redirect_from_error(templates, request, result.error, uuid)

    parent, rows = result.value

    # Making appropriate file name --------------------------------------------
    filename = urllib.parse.quote(parent.name or '??')
    filename = f'Omoide - {filename}.zip'

    # Build payload -----------------------------------------------------------
    assert config
    # locator = infra.FilesystemLocator(
    #     base_folder=config.hot_folder or config.cold_folder,
    #     item=item,
    #     prefix_size=config.prefix_size,
    # )

    # FIXME
    content = (
        '465f066e '
        '267384 '
        '/content/content'
        '/559a52e2-2d97-4e81-a699-af47c0ce79e2'
        '/38/382fb1e1-6b4a-4c41-b821-b405259b9f9d.jpg '
        'blah1.jpg'
    )

    return PlainTextResponse(
        content=content,
        headers={
            'X-Archive-Files': 'zip',
            'Content-Disposition': f'attachment; filename="{filename}"',
        }
    )
