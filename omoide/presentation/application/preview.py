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
    query = infra.query_maker.from_request(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    with infra.Timer() as timer:
        result = await use_case.execute(user, uuid)

    if result.access.does_not_exist:
        raise fastapi.HTTPException(status_code=404)

    if result.access.is_not_given:
        raise fastapi.HTTPException(status_code=401)

    placeholder = utils.make_search_report(
        total=len(result.neighbours),
        duration=timer.seconds,
    )

    context = {
        'request': request,
        'query': query,
        'placeholder': placeholder,
        'item': result.item,
        'result': result,
        'album': infra.Album(
            sequence=result.neighbours,
            position=result.item.uuid,
            items_on_page=constants.PAGES_IN_BLOCK,
        )
    }
    return dependencies.templates.TemplateResponse('preview.html', context)
