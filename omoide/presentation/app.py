"""Application server.

This component is facing towards the user and displays search results.
"""
import os
from contextlib import asynccontextmanager
from typing import Any
from typing import Iterator

from fastapi import APIRouter
from fastapi import Depends
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from omoide.application.controllers import api as api_legacy
from omoide.omoide_api import api_info
from omoide.omoide_api.exif import exif_controllers
from omoide.omoide_api.info import info_controllers
from omoide.omoide_api.input import input_controllers
from omoide.omoide_api.items import item_controllers
from omoide.omoide_api.media import media_controllers
from omoide.omoide_api.metainfo import metainfo_controllers
from omoide.omoide_api.users import users_controllers
from omoide.omoide_app.auth import auth_controllers
from omoide.omoide_app.home import home_controllers
from omoide.omoide_app.search import search_controllers
from omoide.presentation import api as api_old
from omoide.presentation import app_config
from omoide.presentation import application
from omoide.presentation import dependencies as dep


def get_app() -> FastAPI:
    """Create app instance."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # noqa
        """Application lifespan."""
        # Connect to the database
        await dep.get_db().connect()
        yield
        # Disconnect from the database
        await dep.get_db().disconnect()

    new_app = FastAPI(
        lifespan=lifespan,
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )

    # TODO - use only during development
    new_app.mount(
        '/static',
        StaticFiles(directory='omoide/presentation/static'),
        name='static',
    )

    if app_config.Config().env != 'prod':
        new_app.mount(
            '/content',
            StaticFiles(directory=os.environ['OMOIDE_COLD_FOLDER']),
            name='content',
        )

        @new_app.get('/all_routes')
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

    return new_app


def get_api() -> FastAPI:
    """Create API instance."""
    new_api = FastAPI(
        redoc_url=None,
        title='OmoideAPI',
        version=api_info.__version__,
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


def get_middlewares() -> Iterator[tuple[Any, dict[str, Any]]]:
    """Return list of needed middlewares."""
    # CORS
    # TODO - move it to config
    origins = [
        'https://omoide.ru',
        'https://www.omoide.ru',
        'http://localhost',
        'http://localhost:8080',
    ]

    cors_config = dict(
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    yield CORSMiddleware, cors_config


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


def apply_app_routes(current_app: FastAPI) -> None:
    """Register APP routes."""
    current_app.include_router(auth_controllers.auth_router)
    current_app.include_router(home_controllers.home_router)
    current_app.include_router(search_controllers.api_search_router)
    current_app.include_router(search_controllers.app_search_router)

    # legacy
    current_app.include_router(api_legacy.api_media.router)
    current_app.include_router(api_legacy.api_profile.router)

    # Special application routes
    current_app.include_router(application.app_special.router)
    current_app.include_router(application.app_profile.router)

    # API routes
    current_app.include_router(api_old.api_browse.router)
    current_app.include_router(api_old.api_items.router)

    # Application routes
    current_app.include_router(application.app_browse.router)
    current_app.include_router(application.app_home.router)
    current_app.include_router(application.app_item.router)
    current_app.include_router(application.app_preview.router)
    current_app.include_router(application.app_upload.router)


def apply_middlewares(current_app: FastAPI) -> None:
    """Apply middlewares."""
    for middleware_type, middleware_config in get_middlewares():
        current_app.add_middleware(middleware_type, **middleware_config)


app = get_app()
api = get_api()
# TODO - change mounting point after all endpoints will be migrated
app.mount('/api-new', api)
apply_api_routes(api)
apply_app_routes(app)
apply_middlewares(app)
