# -*- coding: utf-8 -*-
"""Preview related routes.
"""
import fastapi
from fastapi.responses import HTMLResponse

from omoide import use_cases
from omoide.domain import auth
from omoide.presentation import dependencies, constants, utils
from omoide.presentation import infra

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

    placeholder = utils.make_search_report(
        total=len(result.neighbours),
        duration=timer.seconds,
    )

    context = {
        'request': request,
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
