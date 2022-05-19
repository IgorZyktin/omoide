# -*- coding: utf-8 -*-
"""Search related routes.
"""
import fastapi
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from omoide import domain
from omoide import use_cases
from omoide.presentation import dependencies, constants
from omoide.presentation import infra
from omoide.presentation import utils
from omoide.presentation.config import config

router = fastapi.APIRouter()

templates = Jinja2Templates(directory='omoide/presentation/templates')


@router.get('/search')
async def search(
        request: fastapi.Request,
        user: domain.User = fastapi.Depends(dependencies.get_current_user),
        use_case: use_cases.SearchUseCase = fastapi.Depends(
            dependencies.get_search_use_case
        ),
        response_class=HTMLResponse,
):
    """Main page of the application."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
        items_per_page_async=constants.ITEMS_PER_UPLOAD,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

    result, is_random = await use_case.execute(user, query, details)

    if is_random:
        template = 'search_random.html'
        paginator = None
    else:
        template = 'search.html'
        paginator = infra.Paginator(
            page=result.page,
            items_per_page=details.items_per_page,
            total_items=result.total_items,
            pages_in_block=constants.PAGES_IN_BLOCK,
        )

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'query': infra.query_maker.QueryWrapper(query, details),
        'details': details,
        'paginator': paginator,
        'result': result,
    }

    return dependencies.templates.TemplateResponse(template, context)


@router.get('/api/random/{items_per_page}')
async def api_random(
        request: fastapi.Request,
        items_per_page: int,
        user: domain.User = fastapi.Depends(dependencies.get_current_user),
        use_case: use_cases.SearchUseCase = fastapi.Depends(
            dependencies.get_search_use_case
        ),
):
    """Return portion of random items."""
    # TODO - random can return repeating items
    details = domain.Details(page=1, anchor=-1, items_per_page=items_per_page)
    query = domain.Query(raw_query='', tags_include=[], tags_exclude=[])
    result, _ = await use_case.execute(user, query, details)
    return utils.to_simple_items(request, result.items)
