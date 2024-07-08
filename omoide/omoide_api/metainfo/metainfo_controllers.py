"""API operations that process item metainfo."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import const
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.metainfo import metainfo_api_models
from omoide.omoide_api.metainfo import metainfo_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web

metainfo_router = APIRouter(prefix='/metainfo', tags=['Metainfo'])


@metainfo_router.get(
    '/{item_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=metainfo_api_models.MetainfoInput,
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
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return metainfo


@metainfo_router.put(
    '/{item_uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=metainfo_api_models.MetainfoInput,
)
async def api_update_metainfo(
    item_uuid: UUID,
    in_metainfo: metainfo_api_models.MetainfoInput,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Update metainfo entry."""
    use_case = metainfo_use_cases.UpdateMetainfoUseCase(mediator)

    metainfo = models.Metainfo(
        created_at=const.DUMMY_TIME,
        updated_at=const.DUMMY_TIME,
        user_time=in_metainfo.user_time,
        content_type=in_metainfo.content_type,
        author=in_metainfo.author,
        author_url=in_metainfo.author_url,
        saved_from_url=in_metainfo.saved_from_url,
        description=in_metainfo.description,
        extras=in_metainfo.extras or {},
        content_size=in_metainfo.content_size,
        preview_size=in_metainfo.preview_size,
        thumbnail_size=in_metainfo.thumbnail_size,
        content_width=in_metainfo.content_width,
        content_height=in_metainfo.content_height,
        preview_width=in_metainfo.preview_width,
        preview_height=in_metainfo.preview_height,
        thumbnail_width=in_metainfo.thumbnail_width,
        thumbnail_height=in_metainfo.thumbnail_height,
    )

    try:
        await use_case.execute(user, item_uuid, metainfo)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return {'result': f'Updated metainfo for item {item_uuid}'}
