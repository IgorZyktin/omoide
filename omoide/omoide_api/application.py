"""Root API application.

All backend stuff is here.
"""
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request

from omoide import const
from omoide.omoide_api import api_info
from omoide.omoide_api.exif import exif_controllers
from omoide.omoide_api.info import info_controllers
from omoide.omoide_api.input import input_controllers
from omoide.omoide_api.items import item_controllers
from omoide.omoide_api.media import media_controllers
from omoide.omoide_api.metainfo import metainfo_controllers
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
                {
                    'path': route.path,
                    'name': route.name
                } for route in request.app.routes
            ]
            return url_list

    return new_api


def apply_api_routes(current_api: FastAPI) -> None:
    """Register API routes."""
    api_router_v1 = APIRouter(prefix='/v1')
    api_router_v1.include_router(exif_controllers.exif_router)
    api_router_v1.include_router(info_controllers.info_router)
    api_router_v1.include_router(input_controllers.input_router)
    api_router_v1.include_router(item_controllers.items_router)
    api_router_v1.include_router(media_controllers.media_router)
    api_router_v1.include_router(metainfo_controllers.metainfo_router)
    api_router_v1.include_router(users_controllers.users_router)

    current_api.include_router(api_router_v1)
