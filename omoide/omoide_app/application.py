"""Root APP application.

All interactions with user are here.
"""

from collections.abc import AsyncGenerator
from collections.abc import Iterator
from contextlib import asynccontextmanager
import os
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from omoide import dependencies as dep
from omoide.omoide_app.auth import auth_controllers
from omoide.omoide_app.browse import browse_controllers
from omoide.omoide_app.home import home_controllers
from omoide.omoide_app.items import item_controllers
from omoide.omoide_app.preview import preview_controllers
from omoide.omoide_app.profile import profile_controllers
from omoide.omoide_app.search import search_controllers
from omoide.omoide_app.special import special_controllers
from omoide.omoide_app.upload import upload_controllers
from omoide.presentation import app_config


def get_app() -> FastAPI:
    """Create app instance."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Application lifespan."""
        _ = app
        await dep.get_database().connect()
        yield
        await dep.get_database().disconnect()

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

    # TODO - stop using two folders for the application
    if app_config.Config().env != 'prod':
        new_app.mount(
            '/content',
            StaticFiles(directory=os.environ['OMOIDE_COLD_FOLDER']),
            name='content',
        )

    return new_app


def apply_app_routes(current_app: FastAPI) -> None:
    """Register APP routes."""
    current_app.include_router(auth_controllers.app_auth_router)
    current_app.include_router(browse_controllers.app_browse_router)
    current_app.include_router(home_controllers.app_home_router)
    current_app.include_router(item_controllers.app_items_router)
    current_app.include_router(preview_controllers.app_preview_router)
    current_app.include_router(profile_controllers.app_profile_router)
    current_app.include_router(search_controllers.app_search_router)
    current_app.include_router(special_controllers.app_special_router)
    current_app.include_router(upload_controllers.app_upload_router)


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
