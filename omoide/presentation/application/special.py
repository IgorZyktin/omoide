# -*- coding: utf-8 -*-
"""Browse related routes.
"""
import fastapi
from fastapi.responses import HTMLResponse

from omoide.presentation import dependencies, infra, constants
from omoide.presentation.config import config
from omoide.domain import auth
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
        'config': config,
        'user': auth.User.new_anon(),
        'query': infra.query_maker.QueryWrapper(query, details),
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
    """Show Not allowed page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)

    context = {
        'request': request,
        'config': config,
        'user': auth.User.new_anon(),
        'query': infra.query_maker.QueryWrapper(query, details),
    }
    return dependencies.templates.TemplateResponse(
        name='not_allowed.html',
        context=context,
        status_code=401,
    )


@router.get('/not_appropriate')
async def not_appropriate(
        request: fastapi.Request,
        response_class=HTMLResponse,
):
    """Show Not appropriate page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)

    context = {
        'request': request,
        'config': config,
        'user': auth.User.new_anon(),
        'query': infra.query_maker.QueryWrapper(query, details),
    }
    return dependencies.templates.TemplateResponse(
        name='not_appropriate.html',
        context=context,
        status_code=400,
    )
