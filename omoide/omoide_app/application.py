"""Root APP application.

All interactions with user are here.
"""

from collections.abc import AsyncGenerator
from collections.abc import Iterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from omoide import dependencies as dep
from omoide.omoide_app.admin import admin_controllers
from omoide.omoide_app.auth import auth_controllers
from omoide.omoide_app.browse import browse_controllers
from omoide.omoide_app.home import home_controllers
from omoide.omoide_app.items import item_controllers
from omoide.omoide_app.preview import preview_controllers
from omoide.omoide_app.profile import profile_controllers
from omoide.omoide_app.search import search_controllers
from omoide.omoide_app.special import special_controllers
from omoide.omoide_app.upload import upload_controllers


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

    config = dep.get_config()

    new_app.mount(
        '/static',
        StaticFiles(directory=config.static_folder),
        name='static',
    )

    if config.env != 'prod':
        new_app.mount(
            '/content',
            StaticFiles(directory=config.data_folder),
            name='content',
        )

    return new_app


def apply_app_routes(current_app: FastAPI) -> None:
    """Register APP routes."""
    current_app.include_router(admin_controllers.app_admin_router)
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
    config = dep.get_config()
    yield (
        CORSMiddleware,
        {
            'allow_origins': config.allowed_origins,
            'allow_credentials': True,
            'allow_methods': ['*'],
            'allow_headers': ['*'],
        },
    )


def apply_middlewares(current_app: FastAPI) -> None:
    """Apply middlewares."""
    for middleware_type, middleware_config in get_middlewares():
        current_app.add_middleware(middleware_type, **middleware_config)
