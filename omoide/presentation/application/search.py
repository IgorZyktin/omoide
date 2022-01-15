# -*- coding: utf-8 -*-
"""Search related routes.
"""
import http

import fastapi
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from omoide import use_cases
from omoide.domain import auth
from omoide.presentation import dependencies
from omoide.presentation.infra import query_maker

router = fastapi.APIRouter()

templates = Jinja2Templates(directory='presentation/templates')


@router.get('/')
@router.get('/search')
@router.post('/search')
async def search(
        request: fastapi.Request,
        user: auth.User = fastapi.Depends(dependencies.get_current_user),
        use_case: use_cases.SearchUseCase = fastapi.Depends(
            dependencies.get_search_use_case
        ),
        response_class=HTMLResponse | RedirectResponse
):
    """Main page of the application."""
    query = query_maker.from_request(request.query_params)

    if request.method == 'POST':
        form = await request.form()
        query = query_maker.from_form(query, form.get('query', ''))
        return RedirectResponse(
            request.url_for('search') + query.as_str(),
            status_code=http.HTTPStatus.SEE_OTHER,
        )

    result = await use_case.execute(user, query.query)

    context = {
        'request': request,
        'query': query,
        'placeholder': 'Enter something',
        'result': result,
    }
    return dependencies.templates.TemplateResponse('search.html', context)
