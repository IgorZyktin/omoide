# -*- coding: utf-8 -*-
"""Search related routes.
"""
import http

import fastapi
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from omoide.presentation.infra import query_maker
from omoide.use_cases import search as search_use_cases

router = fastapi.APIRouter()

templates = Jinja2Templates(directory='presentation/templates')


@router.get('/')
@router.get('/search')
@router.post('/search')
async def search(
        request: fastapi.Request,
        response_class=HTMLResponse | RedirectResponse):
    """Main page of the application."""
    query = query_maker.from_request(request.query_params)

    if request.method == 'POST':
        form = await request.form()
        query = query_maker.from_form(query, form.get('query', ''))
        return RedirectResponse(
            request.url_for('search') + query_maker.as_str(query),
            status_code=http.HTTPStatus.SEE_OTHER,
        )

    if query:
        use_case = search_use_cases.AnonSearchSpecificItemsUseCase()
    else:
        use_case = search_use_cases.AnonSearchRandomItemsUseCase()

    result = await use_case.execute()

    context = {
        'request': request,
        'query': query,
        'placeholder': 'Enter something',
        'result': result,
    }
    return templates.TemplateResponse('search.html', context)
