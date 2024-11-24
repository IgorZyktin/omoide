"""API operations that process item metainfo."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
import pytz

from omoide import dependencies as dep
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.metainfo import metainfo_api_models
from omoide.omoide_api.metainfo import metainfo_use_cases
from omoide.presentation import web

api_metainfo_router = APIRouter(prefix='/metainfo', tags=['Metainfo'])


@api_metainfo_router.get(
    '/{item_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=metainfo_api_models.MetainfoOutput,
)
async def api_read_metainfo(
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Get metainfo."""
    use_case = metainfo_use_cases.ReadMetainfoUseCase(mediator)

    try:
        metainfo = await use_case.execute(user, item_uuid)
    except Exception as exc:
        return web.raise_from_exc(exc)

    if user.timezone is None:
        created_at = metainfo.created_at.isoformat()
        updated_at = metainfo.updated_at.isoformat()
        deleted_at = metainfo.deleted_at.isoformat() if metainfo.deleted_at else None
        user_time = metainfo.user_time.isoformat() if metainfo.user_time else None
    else:
        tz = pytz.timezone(user.timezone or 'UTC')
        created_at = metainfo.created_at.astimezone(tz).isoformat()
        updated_at = metainfo.updated_at.astimezone(tz).isoformat()
        deleted_at = metainfo.deleted_at.astimezone(tz).isoformat() if metainfo.deleted_at else None
        user_time = metainfo.user_time.astimezone(tz).isoformat() if metainfo.user_time else None

    return metainfo_api_models.MetainfoOutput(
        created_at=created_at,
        updated_at=updated_at,
        deleted_at=deleted_at,
        user_time=user_time,
        **metainfo.model_dump(
            exclude={'created_at', 'updated_at', 'deleted_at', 'user_time'},
        ),
    )


@api_metainfo_router.put(
    '/{item_uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str],
)
async def api_update_metainfo(
    item_uuid: UUID,
    metainfo_input: metainfo_api_models.MetainfoInput,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Update metainfo entry."""
    use_case = metainfo_use_cases.UpdateMetainfoUseCase(mediator)

    try:
        await use_case.execute(user, item_uuid, **metainfo_input.model_dump())
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {'result': 'updated metainfo', 'item_uuid': str(item_uuid)}
