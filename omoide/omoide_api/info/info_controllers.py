"""Technical information about the API."""
from fastapi import APIRouter
from fastapi import status

from omoide import const

info_router = APIRouter(prefix='/info', tags=['info'])


@info_router.get(
    '/version',
    status_code=status.HTTP_200_OK,
    response_model=dict[str, str],
)
async def api_get_version():
    """Get current version of the API."""
    return {'version': const.VERSION}
