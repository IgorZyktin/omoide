# -*- coding: utf-8 -*-
"""Specific search by owner uuid.
"""
import fastapi
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from omoide import use_cases
from omoide.domain import auth
from omoide.presentation import dependencies, constants, utils
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
    query = infra.query_maker.from_request(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    with infra.Timer() as timer:
        result = await use_case.execute(user, query.query, uuid)

    paginator = infra.Paginator(
        page=result.page,
        items_per_page=query.query.items_per_page,
        total_items=result.total_items,
        pages_in_block=constants.PAGES_IN_BLOCK,
    )

    placeholder = utils.make_search_report(result.total_items, timer.seconds)

    context = {
        'request': request,
        'query': query,
        'uuid': uuid,
        'placeholder': placeholder,
        'paginator': paginator,
        'result': result,
    }
    return dependencies.templates.TemplateResponse('by_user.html', context)
