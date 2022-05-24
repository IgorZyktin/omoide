# -*- coding: utf-8 -*-
"""Preview related routes.
"""
import fastapi
from fastapi.responses import HTMLResponse, RedirectResponse

from omoide import use_cases, domain
from omoide.domain import auth, exceptions
from omoide.presentation import constants
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation.config import config

router = fastapi.APIRouter()


@router.get('/preview/{uuid}')
async def preview(
        request: fastapi.Request,
        uuid: str,
        user: auth.User = fastapi.Depends(dep.get_current_user),
        use_case: use_cases.PreviewUseCase = fastapi.Depends(
            dep.app_preview_use_case
        ),
        response_class=HTMLResponse,
):
    """Browse contents of a single item as one object."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

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

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'query': infra.query_maker.QueryWrapper(query, details),
        'item': result.item,
        'result': result,
        'album': infra.Album(
            sequence=result.neighbours,
            position=result.item.uuid,
            items_on_page=constants.PAGES_IN_BLOCK,  # TODO: move to details
        ),
        'current_item': result.item,
    }
    return dep.templates.TemplateResponse('preview.html', context)
