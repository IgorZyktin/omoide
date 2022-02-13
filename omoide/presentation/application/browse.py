# -*- coding: utf-8 -*-
"""Browse related routes.
"""
import fastapi
from fastapi.responses import HTMLResponse

from omoide import use_cases
from omoide import domain
from omoide.presentation import dependencies, infra, constants, utils

router = fastapi.APIRouter()


@router.get('/browse/{uuid}')
async def browse(
        request: fastapi.Request,
        uuid: str,
        user: domain.User = fastapi.Depends(dependencies.get_current_user),
        use_case: use_cases.BrowseUseCase = fastapi.Depends(
            dependencies.get_browse_use_case
        ),
        response_class=HTMLResponse,
):
    """Browse contents of a single item as collection."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)

    with infra.Timer() as timer:
        access, result = await use_case.execute(user, uuid, details)

    if access.is_not_given:
        raise fastapi.HTTPException(status_code=401)

    if access.does_not_exist or result is None:
        raise fastapi.HTTPException(status_code=404)

    paginator = infra.Paginator(
        page=result.page,
        items_per_page=details.items_per_page,
        total_items=result.total_items,
        pages_in_block=constants.PAGES_IN_BLOCK,
    )

    placeholder = utils.make_search_report(result.total_items, timer.seconds)

    context = {
        'request': request,
        'uuid': uuid,
        'query': infra.query_maker.QueryWrapper(query, details),
        'placeholder': placeholder,
        'paginator': paginator,
        'result': result,
    }
    return dependencies.templates.TemplateResponse('browse.html', context)
