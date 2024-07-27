"""Media related API operations."""
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.media import media_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web

media_router = APIRouter(prefix='/media', tags=['Media'])


@media_router.delete(
    '',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | int],
)
async def api_delete_processed_media(
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Delete processed media.

    Will delete all records, that were successfully
    processed and had no errors.

    Anons are not allowed to do this. If registered user will request this,
    it will only affect items owned by this user.
    If admin request this, it will delete all processed items.
    """
    use_case = media_use_cases.DeleteProcessedMediaUseCase(mediator)

    try:
        total_rows_affected = await use_case.execute(user)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return {
        'result': 'Deleted all processed Media records',
        'rows': total_rows_affected,
    }
