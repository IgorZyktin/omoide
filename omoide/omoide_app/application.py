"""Root APP application.

All interaction with user goes here.
"""

from collections.abc import Iterator
from contextlib import asynccontextmanager
import os
from typing import Any

from fastapi import FastAPI
from fastapi import Request
from fastapi.staticfiles import StaticFiles

from omoide.omoide_app.auth import auth_controllers
from omoide.omoide_app.browse import browse_controller
from omoide.omoide_app.home import home_controllers
from omoide.omoide_app.items import item_controllers
from omoide.omoide_app.preview import preview_controllers
from omoide.omoide_app.profile import profile_controllers
from omoide.omoide_app.search import search_controllers
from omoide.omoide_app.special import special_controllers
from omoide.omoide_app.upload import upload_controllers
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
                {'path': route.path, 'name': route.name}
                for route in request.app.routes
            ]
            return url_list

    return new_app


def apply_app_routes(current_app: FastAPI) -> None:
    """Register APP routes."""
    current_app.include_router(auth_controllers.app_auth_router)
    current_app.include_router(browse_controller.app_browse_router)
    current_app.include_router(home_controllers.app_home_router)
    current_app.include_router(item_controllers.app_items_router)
    current_app.include_router(preview_controllers.app_preview_router)
    current_app.include_router(profile_controllers.app_profile_router)
    current_app.include_router(search_controllers.app_search_router)
    current_app.include_router(special_controllers.app_special_router)
    current_app.include_router(upload_controllers.app_upload_router)

    # API routes
    current_app.include_router(api_old.api_items.router)

    # APP routes
    current_app.include_router(application.app_item.router)


def get_middlewares() -> Iterator[tuple[Any, dict[str, Any]]]:
    """Return list of needed middlewares."""
    for description in app_config.Config().middlewares:
        if description.name.casefold() == 'CORSMiddleware'.casefold():
            from fastapi.middleware.cors import CORSMiddleware

            yield CORSMiddleware, description.config


def apply_middlewares(current_app: FastAPI) -> None:
    """Apply middlewares."""
    for middleware_type, middleware_config in get_middlewares():
        current_app.add_middleware(middleware_type, **middleware_config)
