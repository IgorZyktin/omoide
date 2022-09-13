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
from omoide.presentation.application import app_item_update
from omoide.presentation.application import auth
from omoide.presentation.application import preview
from omoide.presentation.application import profile
from omoide.presentation.application import search
from omoide.presentation.application import special
from omoide.presentation.application import upload

app = fastapi.FastAPI(
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)


@app.on_event('startup')
async def startup():
    """Connect to the database."""
    await dep.db.connect()


@app.on_event('shutdown')
async def shutdown():
    """Disconnect from the database."""
    await dep.db.disconnect()


app.include_router(auth.router)
app.include_router(preview.router)
app.include_router(search.router)
app.include_router(special.router)
app.include_router(profile.router)
app.include_router(upload.router)

# API routes
app.include_router(api.browse.router)
app.include_router(api.items.router)
app.include_router(api.home.router)
app.include_router(api.api_media.router)
app.include_router(api.api_exif.router)
app.include_router(api.api_meta.router)

# Application routes
app.include_router(application.browse.router)
app.include_router(application.home.router)
app.include_router(application.create_item.router)
app.include_router(application.app_item_update.router)
app.include_router(application.app_item_delete.router)

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
