"""Item related API operations."""

from typing import Annotated
import urllib.parse
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.responses import PlainTextResponse

from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.common import common_api_models
from omoide.omoide_api.items import item_api_models
from omoide.omoide_api.items import item_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web

api_items_router = APIRouter(prefix='/items', tags=['Items'])


@api_items_router.post(
    '',
    status_code=status.HTTP_201_CREATED,
    response_model=common_api_models.OneItemOutput,
)
async def api_create_item(
    request: Request,
    response: Response,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    item_in: item_api_models.ItemInput,
):
    """Get exising item."""
    use_case = item_use_cases.CreateItemsUseCase(mediator)

    try:
        _, items = await use_case.execute(user, [item_in.model_dump()])
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    item = items[0]

    response.headers['Location'] = str(
        request.url_for('api_read_item', item_uuid=item.uuid)
    )

    return common_api_models.OneItemOutput(
        item=common_api_models.ItemOutput(**item.model_dump())
    )


@api_items_router.post(
    '/bulk',
    status_code=status.HTTP_201_CREATED,
    response_model=common_api_models.ManyItemsOutput,
)
async def api_create_many_items(
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    items_in: list[item_api_models.ItemInput],
):
    """Get exising item."""
    use_case = item_use_cases.CreateItemsUseCase(mediator)

    try:
        duration, items = await use_case.execute(
            user=user,
            items_in=[item_in.model_dump() for item_in in items_in],
        )
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return common_api_models.ManyItemsOutput(
        duration=duration,
        items=[
            common_api_models.ItemOutput(**item.model_dump(exclude={'id'}))
            for item in items
        ],
    )


@api_items_router.get(
    '/{item_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.OneItemOutput,
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

    return common_api_models.OneItemOutput(
        item=common_api_models.ItemOutput(**item.model_dump())
    )


@api_items_router.get(
    '',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.ManyItemsOutput,
)
async def api_read_many_items(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    owner_uuid: Annotated[UUID | None, Query()] = None,
    parent_uuid: Annotated[UUID | None, Query()] = None,
    name: Annotated[
        str | None,
        Query(
            max_length=common_api_models.MAX_LENGTH_DEFAULT,
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=common_api_models.MIN_LIMIT,
            lt=common_api_models.MAX_LIMIT,
        ),
    ] = common_api_models.DEFAULT_LIMIT,
):
    """Get exising items."""
    use_case = item_use_cases.ReadManyItemsUseCase(mediator)

    try:
        duration, items = await use_case.execute(
            user=user,
            owner_uuid=owner_uuid,
            parent_uuid=parent_uuid,
            name=name,
            limit=limit,
        )
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return common_api_models.ManyItemsOutput(
        duration=duration,
        items=[
            common_api_models.ItemOutput(**item.model_dump()) for item in items
        ],
    )


@api_items_router.delete(
    '/{item_uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=common_api_models.ItemDeleteOutput,
)
async def api_delete_item(
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Delete exising item."""
    use_case = item_use_cases.DeleteItemUseCase(mediator)

    try:
        parent = await use_case.execute(user, item_uuid)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return common_api_models.ItemDeleteOutput(
        result=f'Deleted item {item_uuid}',
        item_uuid=str(item_uuid),
        switch_to=common_api_models.ItemOutput(**parent.model_dump()),
    )


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


@api_items_router.get('/download/{item_uuid}')
async def api_download_collection(
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    response_class: type[Response] = PlainTextResponse,  # noqa: ARG001
):
    """Return all children as a zip archive.

    WARNING - this endpoint works only behind NGINX with mod_zip installed.
    """
    use_case = item_use_cases.DownloadCollectionUseCase(mediator)

    try:
        lines, owner, item = await use_case.execute(
            user=user,
            item_uuid=item_uuid,
        )
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    filename = urllib.parse.quote(item.name or 'unnamed collection')
    filename = f'Omoide - {filename}'

    return PlainTextResponse(
        content='\n'.join(lines),
        headers={
            'X-Archive-Files': 'zip',
            'Content-Disposition': f'attachment; filename="{filename}.zip"',
        },
    )
