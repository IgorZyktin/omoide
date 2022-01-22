# -*- coding: utf-8 -*-
"""Browse related routes.
"""
import http

import fastapi
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from omoide import use_cases
from omoide.domain import auth
from omoide.presentation import dependencies, infra
from omoide.presentation.infra import query_maker

router = fastapi.APIRouter()


@router.get('/browse/{uuid}')
@router.post('/browse/{uuid}')
async def browse(
        request: fastapi.Request,
        uuid: str,
        user: auth.User = fastapi.Depends(dependencies.get_current_user),
        use_case: use_cases.BrowseUseCase = fastapi.Depends(
            dependencies.get_browse_use_case
        ),
        response_class=HTMLResponse | RedirectResponse):
    """Browse contents of a single item as collection."""
    query = query_maker.from_request(request.query_params)

    if request.method == 'POST':
        form = await request.form()
        query = query_maker.from_form(query, form.get('query', ''))
        return RedirectResponse(
            request.url_for('search') + query.as_str(),
            status_code=http.HTTPStatus.SEE_OTHER,
        )

    result = await use_case.execute(user, uuid, query.query)

    if result.access.does_not_exist:
        raise fastapi.HTTPException(status_code=404)

    if result.access.is_not_given:
        raise fastapi.HTTPException(status_code=401)

    paginator = infra.Paginator(
        page=result.page,
        items_per_page=query.query.items_per_page,
        total_items=result.total_items,
        pages_in_block=10,
    )

    context = {
        'request': request,
        'uuid': uuid,
        'query': query,
        'placeholder': 'Enter something',
        'paginator': paginator,
        'result': result,
    }
    return dependencies.templates.TemplateResponse('browse.html', context)
