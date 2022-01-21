# -*- coding: utf-8 -*-
"""Preview related routes.
"""
import http

import fastapi
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from omoide import use_cases
from omoide.domain import auth
from omoide.presentation import dependencies
from omoide.presentation import infra

router = fastapi.APIRouter()


@router.get('/preview/{uuid}')
@router.post('/preview/{uuid}')
async def preview(
        request: fastapi.Request,
        uuid: str,
        user: auth.User = fastapi.Depends(dependencies.get_current_user),
        use_case: use_cases.PreviewUseCase = fastapi.Depends(
            dependencies.get_preview_use_case
        ),
        response_class=HTMLResponse | RedirectResponse):
    """Browse contents of a single item as one object."""
    query = infra.query_maker.from_request(request.query_params)

    if request.method == 'POST':
        form = await request.form()
        query = infra.query_maker.from_form(query, form.get('query', ''))
        return RedirectResponse(
            request.url_for('search') + query.as_str(),
            status_code=http.HTTPStatus.SEE_OTHER,
        )

    result = await use_case.execute(user, uuid)

    if result.access.does_not_exist:
        raise fastapi.HTTPException(status_code=404)

    if result.access.is_not_given:
        raise fastapi.HTTPException(status_code=401)

    context = {
        'request': request,
        'query': query,
        'placeholder': 'Enter something',
        'item': result.item,
        'result': result,
        'album': infra.Album(
            sequence=result.neighbours,
            position=result.item.uuid,
            items_on_page=10,
        )
    }
    return dependencies.templates.TemplateResponse('preview.html', context)
