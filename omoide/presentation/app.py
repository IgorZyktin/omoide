"""Application server.

This component is facing towards the user and displays search results.
"""
import os

import fastapi
from fastapi import APIRouter
from fastapi import Depends
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from omoide.application.controllers import api
from omoide.omoide_api import controllers
from omoide.presentation import api as api_old
from omoide.presentation import app_config
from omoide.presentation import application
from omoide.presentation import dependencies as dep

app = fastapi.FastAPI(
    # openapi_url=None,
    # docs_url=None,
    # redoc_url=None,
    dependencies=[
        Depends(dep.patch_request),
    ],
)


@app.on_event('startup')
async def startup():
    """Connect to the database."""
    await dep.get_db().connect()


@app.on_event('shutdown')
async def shutdown():
    """Disconnect from the database."""
    await dep.get_db().disconnect()


def apply_middlewares(current_app: FastAPI) -> None:
    """Apply middlewares."""
    origins = [
        'https://omoide.ru',
        'https://www.omoide.ru',
        'http://localhost',
        'http://localhost:8080',
    ]

    current_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )


api_router_v1 = APIRouter(prefix='/api/v1')


def include_api_routes(current_app: FastAPI) -> None:
    """Register API routes."""
    api_router_v1.include_router(controllers.users_router)

    current_app.include_router(api_router_v1)

    current_app.include_router(api.api_exif.router)
    current_app.include_router(api.api_media.router)
    current_app.include_router(api.api_metainfo.router)
    current_app.include_router(api.api_search.router)
    current_app.include_router(api.api_profile.router)


# Special application routes
app.include_router(application.app_auth.router)
app.include_router(application.app_special.router)
app.include_router(application.app_profile.router)

# API routes
app.include_router(api_old.api_browse.router)
app.include_router(api_old.api_home.router)
app.include_router(api_old.api_items.router)
app.include_router(api_old.api_search.router)

# Application routes
app.include_router(application.app_browse.router)
app.include_router(application.app_home.router)
app.include_router(application.app_item.router)
app.include_router(application.app_preview.router)
app.include_router(application.app_search.router)
app.include_router(application.app_upload.router)

# TODO - add app construction function
apply_middlewares(app)
include_api_routes(app)

app.mount(
    '/static',
    StaticFiles(directory='omoide/presentation/static'),
    name='static',
)

if app_config.Config().env != 'prod':
    app.mount(
        '/content',
        StaticFiles(directory=os.environ['OMOIDE_COLD_FOLDER']),
        name='content',
    )

    @app.get('/all_routes')
    def get_all_urls_from_request(request: fastapi.Request):
        url_list = [
            {
                'path': route.path,
                'name': route.name
            } for route in request.app.routes
        ]
        return url_list
