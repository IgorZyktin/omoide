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
from omoide.presentation.config import config

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
    if infra.parse.cast_uuid(uuid) is None:
        # TODO - maybe use UUID type inside use cases?
        url = request.url_for('not_appropriate')
        return fastapi.responses.RedirectResponse(url)

    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)

    with infra.Timer() as timer:
        result = await use_case.execute(user, uuid, details)

    paginator = infra.Paginator(
        page=result.page,
        items_per_page=details.items_per_page,
        total_items=result.total_items,
        pages_in_block=constants.PAGES_IN_BLOCK,
    )

    placeholder = utils.make_search_report(result.total_items, timer.seconds)

    context = {
        'request': request,
        'config': config,
        'query': infra.query_maker.QueryWrapper(query, details),
        'uuid': uuid,
        'placeholder': placeholder,
        'paginator': paginator,
        'result': result,
    }
    return dependencies.templates.TemplateResponse('by_user.html', context)
