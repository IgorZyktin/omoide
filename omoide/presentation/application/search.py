# -*- coding: utf-8 -*-
"""Search related routes.
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


@router.get('/')
@router.get('/search')
async def search(
        request: fastapi.Request,
        user: auth.User = fastapi.Depends(dependencies.get_current_user),
        use_case: use_cases.SearchUseCase = fastapi.Depends(
            dependencies.get_search_use_case
        ),
        response_class=HTMLResponse,
):
    """Main page of the application."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)

    with infra.Timer() as timer:
        result, is_random = await use_case.execute(user, query, details)

    if is_random:
        paginator = None
    else:
        paginator = infra.Paginator(
            page=result.page,
            items_per_page=details.items_per_page,
            total_items=result.total_items,
            pages_in_block=constants.PAGES_IN_BLOCK,
        )

    report = utils.make_search_report(
        total=result.total_items,
        duration=timer.seconds,
    )

    context = {
        'request': request,
        'query': infra.query_maker.QueryWrapper(query, details),
        'placeholder': 'Enter one or more tags here',
        'paginator': paginator,
        'result': result,
        'report': report,
    }
    return dependencies.templates.TemplateResponse('search.html', context)
