# -*- coding: utf-8 -*-
"""Application server.

This component is facing towards the user and displays search results.
"""
import fastapi
from fastapi.staticfiles import StaticFiles

from omoide.presentation import dependencies
from omoide.presentation.application import browse
from omoide.presentation.application import search

app = fastapi.FastAPI(
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)


@app.on_event('startup')
async def startup():
    """Connect to the database."""
    await dependencies.db.connect()


@app.on_event('shutdown')
async def shutdown():
    """Disconnect from the database."""
    await dependencies.db.disconnect()


app.include_router(search.router)
app.include_router(browse.router)

app.mount(
    '/static',
    StaticFiles(directory='presentation/static'),
    name='static',
)

# TODO(i.zyktin): remove after nginx container setup
app.mount(
    '/content',
    StaticFiles(directory='o:\\new\\omoide-media\\'),
    name='content',
)
