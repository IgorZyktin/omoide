"""Downloading related API operations."""

from typing import Annotated
import urllib.parse
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi.responses import PlainTextResponse

from omoide import dependencies as dep
from omoide import models
from omoide.infra import mediators
from omoide.omoide_api.download import download_use_cases
from omoide.presentation import web

api_download_router = APIRouter(tags=['Download'])


@api_download_router.get(
    '/download/{item_uuid}',
    summary='Return all child items as a zip archive',
)
async def api_download_collection(
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[mediators.ItemsMediator, Depends(dep.get_items_mediator)],
    response_class: type[Response] = PlainTextResponse,  # noqa: ARG001
):
    """Return all child items as a zip archive.

    WARNING - this endpoint works only behind NGINX with mod_zip installed.
    """
    use_case = download_use_cases.DownloadCollectionUseCase(mediator)

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
