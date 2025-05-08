"""Item related API operations."""

from typing import Annotated
from typing import Literal
import urllib.parse
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Request
from fastapi import Response
from fastapi import UploadFile
from fastapi import status
from fastapi.responses import PlainTextResponse

from omoide import dependencies as dep
from omoide import limits
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.common import common_api_models
from omoide.omoide_api.items import item_api_models
from omoide.omoide_api.items import item_use_cases
from omoide.presentation import web

api_items_router = APIRouter(prefix='/items', tags=['Items'])


@api_items_router.post(
    '',
    status_code=status.HTTP_201_CREATED,
    response_model=common_api_models.OneItemOutput,
)
async def api_create_item(
    request: Request,
    response: Response,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    item_in: common_api_models.ItemInput,
):
    """Create single item."""
    use_case = item_use_cases.CreateManyItemsUseCase(mediator)

    try:
        items, users_map = await use_case.execute(user, item_in.model_dump())
    except Exception as exc:
        return web.raise_from_exc(exc)

    item = items[0]
    response.headers['Location'] = str(request.url_for('api_get_item', item_uuid=item.uuid))
    return common_api_models.OneItemOutput(item=common_api_models.convert_item(item, users_map))


@api_items_router.post(
    '/bulk',
    status_code=status.HTTP_201_CREATED,
    response_model=common_api_models.ManyItemsOutput,
)
async def api_create_many_items(
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    items_in: list[common_api_models.ItemInput],
):
    """Create many items in one request."""
    use_case = item_use_cases.CreateManyItemsUseCase(mediator)

    try:
        items, users_map = await use_case.execute(
            user,
            *(item_in.model_dump() for item_in in items_in),
        )
    except Exception as exc:
        return web.raise_from_exc(exc)

    return common_api_models.ManyItemsOutput(
        items=common_api_models.convert_items(items, users_map),
    )


@api_items_router.get(
    '/{item_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.OneItemOutput,
)
async def api_get_item(
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Get exising item."""
    use_case = item_use_cases.GetItemUseCase(mediator)

    try:
        item, users_map = await use_case.execute(user, item_uuid)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return common_api_models.OneItemOutput(item=common_api_models.convert_item(item, users_map))


@api_items_router.get(
    '',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.ManyItemsOutput,
)
async def api_get_many_items(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    owner_uuid: Annotated[UUID | None, Query()] = None,
    parent_uuid: Annotated[UUID | None, Query()] = None,
    name: Annotated[str | None, Query(max_length=limits.MAX_QUERY)] = None,
    limit: Annotated[int, Query(ge=limits.MIN_LIMIT, lt=limits.MAX_LIMIT)] = limits.DEF_LIMIT,
):
    """Get exising items."""
    use_case = item_use_cases.GetManyItemsUseCase(mediator)

    try:
        items, users_map = await use_case.execute(
            user=user,
            owner_uuid=owner_uuid,
            parent_uuid=parent_uuid,
            name=name,
            limit=limit,
        )
    except Exception as exc:
        return web.raise_from_exc(exc)

    return common_api_models.ManyItemsOutput(
        items=common_api_models.convert_items(items, users_map),
    )


@api_items_router.patch(
    '/{item_uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str],
)
async def api_update_item(
    item_uuid: UUID,
    item_update_in: item_api_models.ItemUpdateInput,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Update exising item."""
    use_case = item_use_cases.UpdateItemUseCase(mediator)

    try:
        await use_case.execute(
            user=user,
            item_uuid=item_uuid,
            is_collection=item_update_in.is_collection,
        )
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {'result': 'updated item', 'item_uuid': str(item_uuid)}


@api_items_router.put(
    '/{item_uuid}/name',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | int | None],
)
async def api_rename_item(
    item_uuid: UUID,
    item_rename_in: item_api_models.ItemRenameInput,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Rename exising item."""
    use_case = item_use_cases.RenameItemUseCase(mediator)

    try:
        operation_id = await use_case.execute(
            user=user,
            item_uuid=item_uuid,
            name=item_rename_in.name,
        )
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {
        'result': 'enqueued name change',
        'item_uuid': str(item_uuid),
        'operation_id': operation_id,
    }


@api_items_router.put(
    '/{item_uuid}/parent/{new_parent_uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | int | list[int]],
)
async def api_change_parent_item(
    item_uuid: UUID,
    new_parent_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Rename exising item."""
    use_case = item_use_cases.ChangeParentItemUseCase(mediator)

    try:
        operations = await use_case.execute(
            user=user,
            item_uuid=item_uuid,
            new_parent_uuid=new_parent_uuid,
        )
    except Exception as exc:
        return web.raise_from_exc(exc, lang=user.lang)

    return {
        'result': 'changed parent',
        'item_uuid': str(item_uuid),
        'new_parent_uuid': str(new_parent_uuid),
        'operations': operations,
    }


@api_items_router.put(
    '/{item_uuid}/tags',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | int | None],
)
async def api_update_item_tags(
    item_uuid: UUID,
    item_tags_in: item_api_models.ItemUpdateTagsInput,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Update item tags."""
    use_case = item_use_cases.UpdateItemTagsUseCase(mediator)

    try:
        operation_id = await use_case.execute(
            user=user,
            item_uuid=item_uuid,
            tags=item_tags_in.tags,
        )
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {
        'result': 'enqueued tags update',
        'item_uuid': str(item_uuid),
        'operation_id': operation_id,
    }


@api_items_router.delete(
    '/{item_uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=common_api_models.ItemDeleteOutput,
)
async def api_delete_item(
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    desired_switch: Annotated[Literal['parent', 'sibling'], Query()] = 'sibling',
):
    """Delete exising item."""
    use_case = item_use_cases.DeleteItemUseCase(mediator)

    try:
        item = await use_case.execute(
            user=user,
            item_uuid=item_uuid,
            desired_switch=desired_switch,
        )
    except Exception as exc:
        return web.raise_from_exc(exc)

    if item is None:
        switch_to = None
    else:
        switch_to = common_api_models.convert_item(item, {})

    return common_api_models.ItemDeleteOutput(
        result='deleted item',
        item_uuid=str(item_uuid),
        switch_to=switch_to,
    )


@api_items_router.put(
    '/{item_uuid}/permissions',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, bool | str | int | None],
)
async def api_item_update_permissions(
    item_uuid: UUID,
    permissions_in: item_api_models.PermissionsInput,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Change permissions for given item.

    Can affect parents and children.
    """
    use_case = item_use_cases.ChangePermissionsUseCase(mediator)

    try:
        operation_id = await use_case.execute(
            user=user,
            item_uuid=item_uuid,
            permissions=permissions_in.permissions,
            apply_to_parents=permissions_in.apply_to_parents,
            apply_to_children=permissions_in.apply_to_children,
            apply_to_children_as=permissions_in.apply_to_children_as,
        )
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {
        'result': 'enqueued permissions change',
        'item_uuid': str(item_uuid),
        'apply_to_parents': permissions_in.apply_to_parents,
        'apply_to_children': permissions_in.apply_to_children,
        'apply_to_children_as': permissions_in.apply_to_children_as,
        'operation_id': operation_id,
    }


@api_items_router.put(
    '/{item_uuid}/upload',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str],
)
async def api_upload_item(
    request: Request,
    item_uuid: UUID,
    file: UploadFile,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Store content data for given item."""
    ext = str(file.filename).lower().split('.')[-1]
    if ext not in limits.SUPPORTED_EXTENSION:
        extensions = ', '.join(sorted(limits.SUPPORTED_EXTENSION))
        return Response(
            content=f'Only support extensions {extensions}, got {ext!r}',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    use_case = item_use_cases.UploadItemUseCase(mediator)
    features = item_api_models.extract_features(request)
    content = await file.read()

    try:
        await use_case.execute(
            user=user,
            item_uuid=item_uuid,
            file=models.NewFile(
                content=content,
                content_type=str(file.content_type),
                filename=str(file.filename),
                ext=ext,
                features=features,
            ),
        )
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {
        'result': 'enqueued content adding',
        'item_uuid': str(item_uuid),
    }


@api_items_router.get('/download/{item_uuid}')
async def api_download_collection(
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    response_class: type[Response] = PlainTextResponse,  # noqa: ARG001
):
    """Return all children as a zip archive.

    WARNING - this endpoint works only behind NGINX with mod_zip installed.
    """
    use_case = item_use_cases.DownloadCollectionUseCase(mediator)

    try:
        lines, owner, item = await use_case.execute(
            user=user,
            item_uuid=item_uuid,
        )
    except Exception as exc:
        return web.raise_from_exc(exc)

    if item and item.name:
        filename = urllib.parse.quote(item.name)
    else:
        filename = 'unnamed collection'

    filename = f'Omoide - {filename}'

    return PlainTextResponse(
        content='\n'.join(lines),
        headers={
            'X-Archive-Files': 'zip',
            'Content-Disposition': f'attachment; filename="{filename}.zip"',
        },
    )
