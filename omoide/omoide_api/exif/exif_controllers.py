"""EXIF related API operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi import status

from omoide import dependencies as dep
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.exif import exif_api_models
from omoide.omoide_api.exif import exif_use_cases
from omoide.presentation import web

api_exif_router = APIRouter(prefix='/exif', tags=['EXIF'])


@api_exif_router.post(
    '/{item_uuid}',
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, str],
)
async def api_create_exif(
    request: Request,
    response: Response,
    item_uuid: UUID,
    exif: exif_api_models.EXIFModel,
    owner: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Add EXIF data to existing item."""
    use_case = exif_use_cases.CreateEXIFUseCase(mediator)

    try:
        await use_case.execute(owner, item_uuid, exif.exif)
    except Exception as exc:
        return web.raise_from_exc(exc)

    response.headers['Location'] = str(request.url_for('api_read_exif', item_uuid=item_uuid))

    return {'result': 'created exif', 'item_uuid': str(item_uuid)}


@api_exif_router.get(
    '/{item_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=exif_api_models.EXIFModel,
)
async def api_read_exif(
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Read EXIF data for existing item."""
    use_case = exif_use_cases.ReadEXIFUseCase(mediator)

    try:
        exif = await use_case.execute(user, item_uuid)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return exif_api_models.EXIFModel(exif=exif)


@api_exif_router.put(
    '/{item_uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str],
)
async def api_update_exif(
    item_uuid: UUID,
    exif: exif_api_models.EXIFModel,
    owner: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Update EXIF data for existing item.

    If item has no EXIF data at the moment, it will be created.
    """
    use_case = exif_use_cases.UpdateEXIFUseCase(mediator)

    try:
        await use_case.execute(owner, item_uuid, exif.exif)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {'result': 'updated exif', 'item_uuid': str(item_uuid)}


@api_exif_router.delete(
    '/{item_uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str],
)
async def api_delete_exif(
    item_uuid: UUID,
    owner: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Delete EXIF data from exising item."""
    use_case = exif_use_cases.DeleteEXIFUseCase(mediator)

    try:
        await use_case.execute(owner, item_uuid)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {'result': 'deleted exif', 'item_uuid': str(item_uuid)}
