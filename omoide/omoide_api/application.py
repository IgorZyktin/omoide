"""Root API application.

All backend stuff is here.
"""

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request

from omoide import const
from omoide.omoide_api import api_info
from omoide.omoide_api.actions import actions_controllers
from omoide.omoide_api.browse import browse_controllers
from omoide.omoide_api.exif import exif_controllers
from omoide.omoide_api.home import home_controllers
from omoide.omoide_api.info import info_controllers
from omoide.omoide_api.items import item_controllers
from omoide.omoide_api.metainfo import metainfo_controllers
from omoide.omoide_api.search import search_controllers
from omoide.omoide_api.users import users_controllers
from omoide.presentation import app_config


def get_api() -> FastAPI:
    """Create API instance."""
    new_api = FastAPI(
        redoc_url=None,
        title='OmoideAPI',
        version=const.VERSION,
        description=api_info.DESCRIPTION,
        openapi_tags=api_info.TAGS_METADATA,
        license_info={
            'name': 'MIT',
            'url': 'https://opensource.org/license/mit',
        },
    )

    if app_config.Config().env != 'prod':

        @new_api.get('/all_routes')
        def get_all_urls_from_request(request: Request):
            """List all URLs for this Fastapi instance.

            Supposed to be used only for debugging!
            """
            url_list = [
                {'path': route.path, 'name': route.name}
                for route in request.app.routes
            ]
            return url_list

    return new_api


def apply_api_routes_v1(current_api: FastAPI) -> None:
    """Register API routes."""
    api_router_v1 = APIRouter(prefix='/v1')

    api_router_v1.include_router(actions_controllers.api_actions_router)
    api_router_v1.include_router(browse_controllers.api_browse_router)
    api_router_v1.include_router(exif_controllers.api_exif_router)
    api_router_v1.include_router(home_controllers.api_home_router)
    api_router_v1.include_router(info_controllers.api_info_router)
    api_router_v1.include_router(item_controllers.api_items_router)
    api_router_v1.include_router(metainfo_controllers.api_metainfo_router)
    api_router_v1.include_router(search_controllers.api_search_router)
    api_router_v1.include_router(users_controllers.api_users_router)

    current_api.include_router(api_router_v1)
