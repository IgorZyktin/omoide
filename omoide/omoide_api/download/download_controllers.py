"""Downloading related API operations."""

import urllib.parse
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi.responses import PlainTextResponse

from omoide import dependencies as dep
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.omoide_api.download import download_use_cases
from omoide.presentation import web

api_download_router = APIRouter(tags=['Download'])


@api_download_router.get(
    '/download/{item_uuid}',
    summary='Return all child items as a zip archive',
)
async def api_download_collection(  # noqa: PLR0913
    item_uuid: UUID,
    user: models.User = Depends(dep.get_current_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    meta_repo: db_interfaces.AbsMetaRepo = Depends(dep.get_meta_repo),
    signatures_repo: db_interfaces.AbsSignaturesRepo = Depends(dep.get_signatures_repo),
    response_class: type[Response] = PlainTextResponse,  # noqa: ARG001
):
    """Return all child items as a zip archive.

    WARNING - this endpoint works only behind NGINX with mod_zip installed.
    """
    use_case = download_use_cases.DownloadCollectionUseCase(
        database, items_repo, users_repo, meta_repo, signatures_repo
    )

    try:
        lines, _, item = await use_case.execute(
            user=user,
            item_uuid=item_uuid,
        )
    except Exception as exc:
        return web.response_from_exc(exc)

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
