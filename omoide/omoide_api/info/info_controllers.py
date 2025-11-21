"""Technical information about the API."""

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import const
from omoide import dependencies as dep
from omoide import models
from omoide.omoide_api.common import common_api_models

api_info_router = APIRouter(prefix='/info', tags=['Info'])


@api_info_router.get(
    '/version',
    summary='Get current version of the API',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.VersionOutput,
)
async def api_get_version():
    """Get current version of the API."""
    return {'version': const.VERSION}


@api_info_router.get(
    '/whoami',
    summary='Return current user as API sees it',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.WhoAmIOutput,
)
async def api_get_myself(user: Annotated[models.User, Depends(dep.get_current_user)]):
    """Return current user as API sees it."""
    if user.is_anon:
        return {'uuid': None, 'name': 'anon'}
    return {'uuid': str(user.uuid), 'name': user.name}
