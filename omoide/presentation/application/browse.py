# -*- coding: utf-8 -*-
"""Browse related routes.
"""
import fastapi
from fastapi.responses import RedirectResponse, HTMLResponse

from omoide import domain
from omoide import use_cases
from omoide.domain import exceptions
from omoide.presentation import dependencies as dep
from omoide.presentation import infra, constants
from omoide.presentation.config import config

router = fastapi.APIRouter()


@router.get('/browse/{uuid}')
async def browse(
        request: fastapi.Request,
        uuid: str,
        user: domain.User = fastapi.Depends(dep.get_current_user),
        use_case: use_cases.BrowseUseCase = fastapi.Depends(
            dep.get_browse_use_case
        ),
        response_class=HTMLResponse,
):
    """Browse contents of a single item as collection."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)
    aim = domain.aim_from_params(dict(request.query_params))

    try:
        valid_uuid = infra.parse.cast_uuid(uuid)
        result = await use_case.execute(user, valid_uuid, details)
    except exceptions.IncorrectUUID:
        return RedirectResponse(request.url_for('bad_request'))
    except exceptions.NotFound:
        return RedirectResponse(request.url_for('not_found') + f'?q={uuid}')
    except exceptions.Unauthorized:
        return RedirectResponse(request.url_for('unauthorized') + f'?q={uuid}')
    except exceptions.Forbidden:
        return RedirectResponse(request.url_for('forbidden') + f'?q={uuid}')

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
        'uuid': uuid,
        'aim': aim,
        'query': infra.query_maker.QueryWrapper(query, details),
        'paginator': paginator,
        'result': result,
        'current_item': result.item,
    }
    return dep.templates.TemplateResponse('browse.html', context)
