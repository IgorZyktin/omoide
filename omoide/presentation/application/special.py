# -*- coding: utf-8 -*-
"""Browse related routes.
"""
import fastapi
from fastapi.responses import HTMLResponse

from omoide.presentation import dependencies, infra, constants

router = fastapi.APIRouter()


@router.get('/not_found')
async def not_found(
        request: fastapi.Request,
        response_class=HTMLResponse,
):
    """Show Not found page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)

    context = {
        'request': request,
        'query': infra.query_maker.QueryWrapper(query, details),
        'placeholder': 'Enter one or more tags here',
    }
    return dependencies.templates.TemplateResponse(
        name='not_found.html',
        context=context,
        status_code=404,
    )


@router.get('/not_allowed')
async def not_allowed(
        request: fastapi.Request,
        response_class=HTMLResponse,
):
    """Show Not found page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)

    context = {
        'request': request,
        'query': infra.query_maker.QueryWrapper(query, details),
        'placeholder': 'Enter one or more tags here',
    }
    return dependencies.templates.TemplateResponse(
        name='not_allowed.html',
        context=context,
        status_code=401,
    )
