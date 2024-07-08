"""Technical information about the API."""
import http

from fastapi import APIRouter

from omoide import const

info_router = APIRouter(prefix='/info', tags=['info'])


@info_router.get(
    '/version',
    status_code=http.HTTPStatus.OK,
    response_model=dict[str, str],
)
async def api_get_version():
    """Get current version of the API."""
    return {
        'version': const.VERSION,
    }
