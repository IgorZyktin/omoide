"""Item related API operations."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import const
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.items import item_api_models
from omoide.omoide_api.items import item_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web

items_router = APIRouter(prefix='/items', tags=['Items'])


@items_router.get(
    '/{item_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=item_api_models.ItemOutput,
)
async def api_read_item(
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Get exising item."""
    use_case = item_use_cases.ReadItemUseCase(mediator)

    try:
        item = await use_case.execute(user, item_uuid)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return item_api_models.ItemOutput(**item.model_dump())


@items_router.delete(
    '/{item_uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str],
)
async def api_delete_item(
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Delete exising item."""
    use_case = item_use_cases.DeleteItemUseCase(mediator)

    try:
        parent_uuid = await use_case.execute(user, item_uuid)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    # TODO - actually we can return not only
    #  parent but also next item in collection
    return {
        'result': f'Deleted item {item_uuid}',
        'item_uuid': str(item_uuid),
        'parent_uuid': str(parent_uuid),
    }


@items_router.put(
    '/{item_uuid}/content',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | int],
)
async def api_upload_item_content(
    item_uuid: UUID,
    media: item_api_models.MediaInput,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Store content data for given item.

    Operation is asynchronous, you will get job_id in response.
    """
    use_case = item_use_cases.UploadContentForItemUseCase(mediator)

    try:
        raw_media = models.RawMedia(
            media_type=const.CONTENT,
            content=media.binary_content,
            ext=media.ext,
        )
        media_id = await use_case.execute(user, item_uuid, raw_media)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return {
        'result': 'Created content media record',
        'item_uuid': str(item_uuid),
        'media_id': media_id,
    }


@items_router.put(
    '/{item_uuid}/preview',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | int],
)
async def api_upload_item_preview(
    item_uuid: UUID,
    media: item_api_models.MediaInput,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Store preview data for given item.

    Operation is asynchronous, you will get job_id in response.
    """
    use_case = item_use_cases.UploadPreviewForItemUseCase(mediator)

    try:
        raw_media = models.RawMedia(
            media_type=const.PREVIEW,
            content=media.binary_content,
            ext=media.ext,
        )
        media_id = await use_case.execute(user, item_uuid, raw_media)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return {
        'result': 'Created preview media record',
        'item_uuid': str(item_uuid),
        'media_id': media_id,
    }


@items_router.put(
    '/{item_uuid}/thumbnail',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | int],
)
async def api_upload_item_thumbnail(
    item_uuid: UUID,
    media: item_api_models.MediaInput,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Store thumbnail data for given item.

    Operation is asynchronous, you will get job_id in response.
    """
    use_case = item_use_cases.UploadContentForItemUseCase(mediator)

    try:
        raw_media = models.RawMedia(
            media_type=const.THUMBNAIL,
            content=media.binary_content,
            ext=media.ext,
        )
        media_id = await use_case.execute(user, item_uuid, raw_media)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return {
        'result': 'Created thumbnail media record',
        'item_uuid': str(item_uuid),
        'media_id': media_id,
    }
