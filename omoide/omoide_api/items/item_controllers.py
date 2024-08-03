"""Item related API operations."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.items import item_api_models
from omoide.omoide_api.items import item_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web

api_items_router = APIRouter(prefix='/items', tags=['Items'])


@api_items_router.get(
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


@api_items_router.delete(
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


# TODO - instead of sending data as base64 encoded string
#  we need to switch to file sending
@api_items_router.put(
    '/{item_uuid}/content',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str],
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
        await use_case.execute(
            user=user,
            item_uuid=item_uuid,
            binary_content=media.binary_content,
            ext=media.ext,
        )
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return {
        'result': 'Enqueued content adding',
        'item_uuid': str(item_uuid),
    }


# TODO - previews are not supposed to be sent.
#  They must be generated on the backend
@api_items_router.put(
    '/{item_uuid}/preview',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str],
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
        await use_case.execute(
            user=user,
            item_uuid=item_uuid,
            binary_content=media.binary_content,
            ext=media.ext,
        )
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return {
        'result': 'Enqueued preview adding',
        'item_uuid': str(item_uuid),
    }


# TODO - previews are not supposed to be sent.
#  They must be generated on the backend
@api_items_router.put(
    '/{item_uuid}/thumbnail',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str],
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
    use_case = item_use_cases.UploadThumbnailForItemUseCase(mediator)

    try:
        await use_case.execute(
            user=user,
            item_uuid=item_uuid,
            binary_content=media.binary_content,
            ext=media.ext,
        )
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return {
        'result': 'Enqueued thumbnail adding',
        'item_uuid': str(item_uuid),
    }
