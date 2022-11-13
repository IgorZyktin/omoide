# -*- coding: utf-8 -*-
"""Application server.

This component is facing towards the user and displays search results.
"""
import os

import fastapi
from fastapi.staticfiles import StaticFiles

from omoide.presentation import api
from omoide.presentation import app_config
from omoide.presentation import application
from omoide.presentation import dependencies as dep

app = fastapi.FastAPI(
    # openapi_url=None,
    # docs_url=None,
    # redoc_url=None,
)


@app.on_event('startup')
async def startup():
    """Connect to the database."""
    await dep.db.connect()


@app.on_event('shutdown')
async def shutdown():
    """Disconnect from the database."""
    await dep.db.disconnect()


app.include_router(application.auth.router)
app.include_router(application.special.router)
app.include_router(application.profile.router)

# API routes
app.include_router(api.api_browse.router)
app.include_router(api.api_exif.router)
app.include_router(api.api_home.router)
app.include_router(api.api_items.router)
app.include_router(api.api_media.router)
app.include_router(api.api_metainfo.router)

# Application routes
app.include_router(application.app_browse.router)
app.include_router(application.app_home.router)
app.include_router(application.app_item.router)
app.include_router(application.app_preview.router)
app.include_router(application.app_search.router)
app.include_router(application.app_upload.router)

app.mount(
    '/static',
    StaticFiles(directory='omoide/presentation/static'),
    name='static',
)

if app_config.get_config().env != 'prod':
    app.mount(
        '/content',
        StaticFiles(directory=os.environ['OMOIDE_COLD_FOLDER']),
        name='content',
    )
