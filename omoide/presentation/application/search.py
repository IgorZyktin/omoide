# -*- coding: utf-8 -*-
"""Search related routes.
"""
import fastapi
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from omoide import domain
from omoide import use_cases
from omoide.presentation import dependencies, constants, utils
from omoide.presentation import infra
from omoide.presentation.config import config

router = fastapi.APIRouter()

templates = Jinja2Templates(directory='omoide/presentation/templates')


@router.get('/')
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
        items_per_page_async=constants.ITEMS_PER_PAGE_ASYNC,
    )

    query = infra.query_maker.from_request(request.query_params)

    with infra.Timer() as timer:
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

    report = utils.make_search_report(
        total=result.total_items,
        duration=timer.seconds,
    )

    context = {
        'request': request,
        'config': config,
        'user': user,
        'query': infra.query_maker.QueryWrapper(query, details),
        'details': details,
        'placeholder': 'Enter one or more tags here',
        'paginator': paginator,
        'result': result,
        'report': report,
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

    simple_items = []
    for item in result.items:
        if item.is_collection:
            href = request.url_for('browse', uuid=item.uuid)
        else:
            href = request.url_for('preview', uuid=item.uuid)

        if item.thumbnail_ext is None:
            thumbnail = request.url_for('static', path='empty.png')
        else:
            thumbnail = (
                f'/content/{item.owner_uuid}/thumbnail/{item.thumbnail_path}'
            )

        simple_item = {
            'uuid': item.uuid,
            'name': item.name,
            'is_collection': item.is_collection,
            'href': href,
            'thumbnail': thumbnail,
        }

        simple_items.append(simple_item)

    return simple_items
