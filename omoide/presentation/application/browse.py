# -*- coding: utf-8 -*-
"""Browse related routes.
"""

import fastapi
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = fastapi.APIRouter()

templates = Jinja2Templates(directory='presentation/templates')


@router.get('/browse/{uuid}')
@router.post('/browse/{uuid}')
async def browse(
        request: fastapi.Request,
        uuid: str,
        response_class=HTMLResponse | RedirectResponse):
    """Browse contents of a single item as collection."""
    return HTMLResponse(f'Got {uuid} to browse')


@router.get('/preview/{uuid}')
@router.post('/preview/{uuid}')
async def preview(
        request: fastapi.Request,
        uuid: str,
        response_class=HTMLResponse | RedirectResponse):
    """Browse contents of a single item as one object."""
    return HTMLResponse(f'Got {uuid} to preview')
