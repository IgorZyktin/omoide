"""Item related API operations."""

from collections.abc import AsyncIterator
from typing import Annotated
from typing import Any
from typing import Literal
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Request
from fastapi import Response
from fastapi import UploadFile
from fastapi import status

from omoide import const
from omoide import dependencies as dep
from omoide import exceptions
from omoide import limits
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.object_storage import interfaces as object_interfaces
from omoide.omoide_api.common import common_api_models
from omoide.omoide_api.items import item_api_models
from omoide.omoide_api.items import item_use_cases

api_items_router = APIRouter(prefix='/items', tags=['Items'])


@api_items_router.post(
    '',
    summary='Create single item',
    status_code=status.HTTP_201_CREATED,
    response_model=common_api_models.OneItemOutput,
)
async def api_create_item(  # noqa: PLR0913
    request: Request,
    response: Response,
    item_in: common_api_models.ItemInput,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    meta_repo: db_interfaces.AbsMetaRepo = Depends(dep.get_meta_repo),
    tags_repo: db_interfaces.AbsTagsRepo = Depends(dep.get_tags_repo),
) -> common_api_models.OneItemOutput:
    """Create single item."""
    use_case = item_use_cases.CreateManyItemsUseCase(
        database, items_repo, users_repo, meta_repo, tags_repo
    )

    result = await use_case.execute(user, item_in.model_dump())

    item = result.items[0]
    response.headers['Location'] = str(request.url_for('api_get_item', item_uuid=item.uuid))
    return common_api_models.OneItemOutput(
        item=common_api_models.convert_item(item, result.users_map)
    )


@api_items_router.post(
    '/bulk',
    summary='Create many items in one request',
    status_code=status.HTTP_201_CREATED,
    response_model=common_api_models.ManyItemsOutput,
)
async def api_create_many_items(  # noqa: PLR0913
    items_in: list[common_api_models.ItemInput],
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    meta_repo: db_interfaces.AbsMetaRepo = Depends(dep.get_meta_repo),
    tags_repo: db_interfaces.AbsTagsRepo = Depends(dep.get_tags_repo),
) -> common_api_models.ManyItemsOutput:
    """Create many items in one request."""
    use_case = item_use_cases.CreateManyItemsUseCase(
        database, items_repo, users_repo, meta_repo, tags_repo
    )

    result = await use_case.execute(
        user,
        *(item_in.model_dump() for item_in in items_in),
    )

    return common_api_models.ManyItemsOutput(
        items=common_api_models.convert_items(result.items, result.users_map),
    )


@api_items_router.get(
    '/{item_uuid}',
    summary='Get exising item',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.OneItemOutput,
)
async def api_get_item(
    item_uuid: UUID,
    user: models.User = Depends(dep.get_current_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
) -> common_api_models.OneItemOutput:
    """Get exising item."""
    use_case = item_use_cases.GetItemUseCase(database, items_repo, users_repo)

    result = await use_case.execute(user, item_uuid)

    return common_api_models.OneItemOutput(
        item=common_api_models.convert_item(result.item, result.users_map)
    )


@api_items_router.get(
    '',
    summary='Get list of exising items',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.ManyItemsOutput,
)
async def api_get_many_items(  # noqa: PLR0913
    user: models.User = Depends(dep.get_current_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    owner_uuid: Annotated[UUID | None, Query()] = None,
    parent_uuid: Annotated[UUID | None, Query()] = None,
    name: Annotated[str | None, Query(max_length=limits.MAX_QUERY)] = None,
    limit: Annotated[int, Query(ge=limits.MIN_LIMIT, lt=limits.MAX_LIMIT)] = limits.DEF_LIMIT,
) -> common_api_models.ManyItemsOutput:
    """Get list of exising items."""
    use_case = item_use_cases.GetManyItemsUseCase(database, items_repo, users_repo)

    result = await use_case.execute(
        user=user,
        owner_uuid=owner_uuid,
        parent_uuid=parent_uuid,
        name=name,
        limit=limit,
    )

    return common_api_models.ManyItemsOutput(
        items=common_api_models.convert_items(result.items, result.users_map),
    )


@api_items_router.patch(
    '/{item_uuid}',
    summary='Update exising item',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str],
)
async def api_update_item(
    item_uuid: UUID,
    item_update_in: item_api_models.ItemUpdateInput,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
) -> dict[str, str]:
    """Update exising item."""
    use_case = item_use_cases.UpdateItemUseCase(database, items_repo)

    await use_case.execute(
        user=user,
        item_uuid=item_uuid,
        is_collection=item_update_in.is_collection,
    )

    return {'result': 'updated item', 'item_uuid': str(item_uuid)}


@api_items_router.put(
    '/{item_uuid}/name',
    summary='Rename exising item',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | int | None],
)
async def api_rename_item(
    item_uuid: UUID,
    item_rename_in: item_api_models.ItemRenameInput,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    misc_repo: db_interfaces.AbsMiscRepo = Depends(dep.get_misc_repo),
) -> dict[str, Any]:
    """Rename exising item."""
    use_case = item_use_cases.RenameItemUseCase(database, items_repo, misc_repo)

    operation_id = await use_case.execute(
        user=user,
        item_uuid=item_uuid,
        name=item_rename_in.name,
    )

    return {
        'result': 'enqueued name change',
        'item_uuid': str(item_uuid),
        'operation_id': operation_id,
    }


@api_items_router.put(
    '/{item_uuid}/parent/{new_parent_uuid}',
    summary='Change parent of the item',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | int | list[int]],
)
async def api_change_parent_item(  # noqa: PLR0913
    item_uuid: UUID,
    new_parent_uuid: UUID,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    meta_repo: db_interfaces.AbsMetaRepo = Depends(dep.get_meta_repo),
    misc_repo: db_interfaces.AbsMiscRepo = Depends(dep.get_misc_repo),
    object_storage: object_interfaces.AbsObjectStorage = Depends(dep.get_object_storage),
) -> dict[str, Any]:
    """Change parent of the item."""
    use_case = item_use_cases.ChangeParentItemUseCase(
        database, items_repo, users_repo, meta_repo, misc_repo, object_storage
    )

    operations = await use_case.execute(
        user=user,
        item_uuid=item_uuid,
        new_parent_uuid=new_parent_uuid,
    )

    return {
        'result': 'changed parent',
        'item_uuid': str(item_uuid),
        'new_parent_uuid': str(new_parent_uuid),
        'operations': operations,
    }


@api_items_router.put(
    '/{item_uuid}/tags',
    summary='Update item tags',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | int | None],
)
async def api_update_item_tags(
    item_uuid: UUID,
    item_tags_in: item_api_models.ItemUpdateTagsInput,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    misc_repo: db_interfaces.AbsMiscRepo = Depends(dep.get_misc_repo),
) -> dict[str, Any]:
    """Update item tags."""
    use_case = item_use_cases.UpdateItemTagsUseCase(database, items_repo, misc_repo)

    operation_id = await use_case.execute(
        user=user,
        item_uuid=item_uuid,
        tags=item_tags_in.tags,
    )

    return {
        'result': 'enqueued tags update',
        'item_uuid': str(item_uuid),
        'operation_id': operation_id,
    }


@api_items_router.delete(
    '/{item_uuid}',
    summary='Delete exising item',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=common_api_models.ItemDeleteOutput,
)
async def api_delete_item(  # noqa: PLR0913
    item_uuid: UUID,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    meta_repo: db_interfaces.AbsMetaRepo = Depends(dep.get_meta_repo),
    tags_repo: db_interfaces.AbsTagsRepo = Depends(dep.get_tags_repo),
    object_storage: object_interfaces.AbsObjectStorage = Depends(dep.get_object_storage),
    desired_switch: Annotated[Literal['parent', 'sibling'], Query()] = 'sibling',
) -> common_api_models.ItemDeleteOutput:
    """Delete exising item."""
    use_case = item_use_cases.DeleteItemUseCase(
        database, items_repo, users_repo, meta_repo, tags_repo, object_storage
    )

    item = await use_case.execute(
        user=user,
        item_uuid=item_uuid,
        desired_switch=desired_switch,
    )

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
    summary='Change permissions for given item',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, bool | str | int | None],
)
async def api_item_update_permissions(  # noqa: PLR0913
    item_uuid: UUID,
    permissions_in: item_api_models.PermissionsInput,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    misc_repo: db_interfaces.AbsMiscRepo = Depends(dep.get_misc_repo),
) -> dict[str, Any]:
    """Change permissions for given item.

    Can affect parents and children.
    """
    use_case = item_use_cases.ChangePermissionsUseCase(database, items_repo, users_repo, misc_repo)

    operation_id = await use_case.execute(
        user=user,
        item_uuid=item_uuid,
        permissions=permissions_in.permissions,
        apply_to_parents=permissions_in.apply_to_parents,
        apply_to_children=permissions_in.apply_to_children,
        apply_to_children_as=permissions_in.apply_to_children_as,
    )

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
    summary='Store content data for given item',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str],
)
async def api_upload_item(  # noqa: PLR0913
    request: Request,
    item_uuid: UUID,
    file: UploadFile,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    meta_repo: db_interfaces.AbsMetaRepo = Depends(dep.get_meta_repo),
    misc_repo: db_interfaces.AbsMiscRepo = Depends(dep.get_misc_repo),
    upload_staging: object_interfaces.AbsUploadStaging = Depends(dep.get_upload_staging),
) -> dict[str, Any]:
    """Store content data for given item."""
    ext = str(file.filename).lower().split('.')[-1]
    if ext not in limits.SUPPORTED_EXTENSION:
        extensions = ', '.join(sorted(limits.SUPPORTED_EXTENSION))
        msg = f'Only support extensions {extensions}, got {ext!r}'
        raise exceptions.InvalidInputError(msg)

    use_case = item_use_cases.UploadItemUseCase(database, items_repo, meta_repo, misc_repo)
    features = item_api_models.extract_features(request)

    async def _chunks() -> AsyncIterator[bytes]:
        while True:
            chunk = await file.read(const.UPLOAD_CHUNK_SIZE)
            if not chunk:
                break
            yield chunk

    async with upload_staging.stage(_chunks()) as staged:
        await use_case.execute(
            user=user,
            item_uuid=item_uuid,
            file=models.NewFile(
                content=staged,
                content_type=str(file.content_type),
                filename=str(file.filename),
                ext=ext,
                features=features,
            ),
        )

    return {'result': 'enqueued content adding', 'item_uuid': str(item_uuid)}
