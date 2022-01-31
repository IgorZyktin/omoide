# -*- coding: utf-8 -*-
"""Specific search by owner uuid.
"""
import fastapi
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from omoide import use_cases
from omoide.domain import auth
from omoide.presentation import dependencies
from omoide.presentation import infra

router = fastapi.APIRouter()

templates = Jinja2Templates(directory='presentation/templates')


@router.get('/by_user/{uuid}')
async def by_user(
        request: fastapi.Request,
        uuid: str,
        user: auth.User = fastapi.Depends(dependencies.get_current_user),
        use_case: use_cases.ByUserUseCase = fastapi.Depends(
            dependencies.get_by_user_use_case
        ),
        response_class=HTMLResponse,
):
    """Specific search by owner uuid."""
    query = infra.query_maker.from_request(request.query_params)

    result = await use_case.execute(user, query.query, uuid)

    paginator = infra.Paginator(
        page=result.page,
        items_per_page=query.query.items_per_page,
        total_items=result.total_items,
        pages_in_block=10,
    )

    context = {
        'request': request,
        'query': query,
        'uuid': uuid,
        'placeholder': 'Enter something',
        'paginator': paginator,
        'result': result,
    }
    return dependencies.templates.TemplateResponse('by_user.html', context)
