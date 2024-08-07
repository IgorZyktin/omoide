"""Item related API operations."""
import urllib.parse
from typing import Type
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from starlette.responses import PlainTextResponse

from omoide import models
from omoide import use_cases
from omoide import interfaces
from omoide.infra.special_types import Failure
from omoide.presentation import api_models
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

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


def _convert_rows_to_strings_for_mod_zip(
        rows: list[dict[str, UUID | str | int]],
        prefix_size: int,
        owner_uuid: UUID,
) -> list[str]:
    """Convert data into format of mod_zip."""
    lines: list[str] = []
    total = len(rows)
    digits = len(str(total))
    template = f'{{:0{digits}d}}'
    basic_prefix = '/content/content'

    for i, row in enumerate(rows, start=1):
        item_uuid = str(row['uuid'])
        prefix = item_uuid[:prefix_size]
        content_ext = str(row['content_ext'])

        fs_path = (
            f'{basic_prefix}/{owner_uuid}/{prefix}/{item_uuid}.{content_ext}'
        )

        user_visible_filename = (
            f'{template.format(i)}___{item_uuid}.{content_ext}'
        )

        checksum = row.get('crc32') or '-'
        size = row['content_size'] or 0

        mod_zip_line = (
            f'{checksum} {size} {fs_path} {user_visible_filename}'
        )

        lines.append(mod_zip_line)

    return lines


@router.get('/download/{uuid}')
async def api_items_download(
        request: Request,
        uuid: UUID,
        user: models.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ApiItemsDownloadUseCase = Depends(
            dep.api_items_download_use_case),
        config: Config = Depends(dep.get_config),
        response_class: Type[Response] = PlainTextResponse,
):
    """Return all children as zip archive.

    WARNING - this endpoint works only behind NGINX with mod_zip installed.
    """
    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        return web.redirect_from_error(request, result.error, uuid)

    parent, rows = result.value

    filename = urllib.parse.quote(parent.name or '??')
    filename = f'Omoide - {filename}'

    lines = _convert_rows_to_strings_for_mod_zip(
        rows=rows,
        prefix_size=config.prefix_size,
        owner_uuid=parent.owner_uuid,
    )

    return PlainTextResponse(
        content='\n'.join(lines),
        headers={
            'X-Archive-Files': 'zip',
            'Content-Disposition': f'attachment; filename="{filename}.zip"',
        }
    )
