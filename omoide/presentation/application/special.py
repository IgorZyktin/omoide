# -*- coding: utf-8 -*-
"""Browse related routes.
"""
import http

import fastapi
from fastapi import Request, Depends
from fastapi.responses import HTMLResponse

from omoide import domain
from omoide.presentation import dependencies as dep
from omoide.presentation import infra, constants
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/not_found')
async def not_found(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
        response_class=HTMLResponse,
):
    """Show <not found> page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'query': infra.query_maker.QueryWrapper(query, details),
    }
    return dep.templates.TemplateResponse(
        name='exc_not_found.html',
        context=context,
        status_code=http.HTTPStatus.NOT_FOUND,
    )


@router.get('/unauthorized')
async def unauthorized(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
        response_class=HTMLResponse,
):
    """Show <unauthorized> page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'query': infra.query_maker.QueryWrapper(query, details),
    }
    return dep.templates.TemplateResponse(
        name='exc_unauthorized.html',
        context=context,
        status_code=http.HTTPStatus.UNAUTHORIZED,
    )


@router.get('/forbidden')
async def forbidden(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
        response_class=HTMLResponse,
):
    """Show <forbidden> page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'query': infra.query_maker.QueryWrapper(query, details),
    }
    return dep.templates.TemplateResponse(
        name='exc_forbidden.html',
        context=context,
        status_code=http.HTTPStatus.FORBIDDEN,
    )


@router.get('/bad_request')
async def bad_request(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
        response_class=HTMLResponse,
):
    """Show <bad request> page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'query': infra.query_maker.QueryWrapper(query, details),
    }
    return dep.templates.TemplateResponse(
        name='exc_bad_request.html',
        context=context,
        status_code=http.HTTPStatus.BAD_REQUEST,
    )
