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
from omoide.infra import mediators
from omoide.omoide_api.exif import exif_api_models
from omoide.omoide_api.exif import exif_use_cases
from omoide.presentation import web

api_exif_router = APIRouter(prefix='/exif', tags=['EXIF'])


@api_exif_router.post(
    '/{item_uuid}',
    summary='Add EXIF data to existing item',
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {'description': 'Created'},
        status.HTTP_403_FORBIDDEN: {'description': 'Permission denied'},
        status.HTTP_404_NOT_FOUND: {'description': 'Object does not exist'},
        status.HTTP_409_CONFLICT: {'description': 'Object already exists'},
    },
    response_model=dict[str, str],
)
async def api_create_exif(
    request: Request,
    response: Response,
    item_uuid: UUID,
    exif_in: exif_api_models.EXIFIn,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[mediators.EXIFMediator, Depends(dep.get_exif_mediator)],
):
    """Add EXIF data to existing item."""
    use_case = exif_use_cases.CreateEXIFUseCase(mediator)

    exif = models.Exif(exif=exif_in.exif)

    try:
        await use_case.execute(user, item_uuid, exif)
    except Exception as exc:
        return web.response_from_exc(exc)

    response.headers['Location'] = str(request.url_for('api_read_exif', item_uuid=item_uuid))

    return {'result': 'created exif', 'item_uuid': str(item_uuid)}


@api_exif_router.get(
    '/{item_uuid}',
    summary='Read EXIF data of existing item',
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {'description': 'Ok'},
        status.HTTP_403_FORBIDDEN: {'description': 'Permission denied'},
        status.HTTP_404_NOT_FOUND: {'description': 'Object does not exist'},
    },
    response_model=exif_api_models.EXIFIn,
)
async def api_read_exif(
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[mediators.EXIFMediator, Depends(dep.get_exif_mediator)],
):
    """Read EXIF data of existing item."""
    use_case = exif_use_cases.ReadEXIFUseCase(mediator)

    try:
        exif = await use_case.execute(user, item_uuid)
    except Exception as exc:
        return web.response_from_exc(exc)

    return exif_api_models.EXIFIn(exif=exif)


@api_exif_router.put(
    '/{item_uuid}',
    summary='Update EXIF data of existing item',
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_202_ACCEPTED: {'description': 'Accepted'},
        status.HTTP_403_FORBIDDEN: {'description': 'Permission denied'},
        status.HTTP_404_NOT_FOUND: {'description': 'Object does not exist'},
        status.HTTP_409_CONFLICT: {'description': 'Object already exists'},
    },
    response_model=dict[str, str],
)
async def api_update_exif(
    item_uuid: UUID,
    exif_in: exif_api_models.EXIFIn,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[mediators.EXIFMediator, Depends(dep.get_exif_mediator)],
):
    """Update EXIF data of existing item.

    If item has no EXIF data at the moment, it will be created.
    """
    use_case = exif_use_cases.UpdateEXIFUseCase(mediator)

    exif = models.Exif(exif=exif_in.exif)

    try:
        await use_case.execute(user, item_uuid, exif)
    except Exception as exc:
        return web.response_from_exc(exc)

    return {'result': 'updated exif', 'item_uuid': str(item_uuid)}


@api_exif_router.delete(
    '/{item_uuid}',
    summary='Delete EXIF data of exising item',
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_202_ACCEPTED: {'description': 'Accepted'},
        status.HTTP_403_FORBIDDEN: {'description': 'Permission denied'},
        status.HTTP_404_NOT_FOUND: {'description': 'Object does not exist'},
    },
    response_model=dict[str, str],
)
async def api_delete_exif(
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[mediators.EXIFMediator, Depends(dep.get_exif_mediator)],
):
    """Delete EXIF data of exising item."""
    use_case = exif_use_cases.DeleteEXIFUseCase(mediator)

    try:
        await use_case.execute(user, item_uuid)
    except Exception as exc:
        return web.response_from_exc(exc)

    return {'result': 'deleted exif', 'item_uuid': str(item_uuid)}
