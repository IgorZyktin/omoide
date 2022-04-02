# -*- coding: utf-8 -*-
"""Preview related routes.
"""
import fastapi
from fastapi.responses import HTMLResponse

from omoide import use_cases
from omoide.domain import auth
from omoide.presentation import dependencies, constants, utils
from omoide.presentation import infra
from omoide.presentation.config import config

router = fastapi.APIRouter()


@router.get('/preview/{uuid}')
async def preview(
        request: fastapi.Request,
        uuid: str,
        user: auth.User = fastapi.Depends(dependencies.get_current_user),
        use_case: use_cases.PreviewUseCase = fastapi.Depends(
            dependencies.get_preview_use_case
        ),
        response_class=HTMLResponse,
):
    """Browse contents of a single item as one object."""
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
        access, result = await use_case.execute(user, uuid, details)

    if access.does_not_exist or result is None:
        url = request.url_for('not_found') + f'?q={uuid}'
        return fastapi.responses.RedirectResponse(url)

    if access.is_not_given:
        url = request.url_for('not_allowed') + f'?q={uuid}'
        return fastapi.responses.RedirectResponse(url)

    placeholder = utils.make_search_report(
        total=len(result.neighbours),
        duration=timer.seconds,
    )

    context = {
        'request': request,
        'config': config,
        'user': user,
        'query': infra.query_maker.QueryWrapper(query, details),
        'placeholder': placeholder,
        'item': result.item,
        'result': result,
        'album': infra.Album(
            sequence=result.neighbours,
            position=result.item.uuid,
            items_on_page=constants.PAGES_IN_BLOCK,  # TODO: move to details
        )
    }
    return dependencies.templates.TemplateResponse('preview.html', context)
