# -*- coding: utf-8 -*-
"""Routes related to media upload.
"""
from uuid import UUID

import fastapi
from fastapi import Depends, Request, UploadFile, Form, File
from starlette import status

from omoide import domain, use_cases, utils
from omoide.presentation import dependencies as dep
from omoide.presentation import infra, constants
from omoide.presentation.config import config

router = fastapi.APIRouter()


@router.get('/upload')
async def upload_get(
        request: Request,
        parent_uuid: str = '',
        user: domain.User = Depends(dep.get_current_user),
):
    """Upload media page."""
    if user.is_anon():  # TODO - move it to a separate decorator
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect login or password',
            headers={'WWW-Authenticate': 'Basic realm="omoide"'},
        )

    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)

    if not utils.is_valid_uuid(parent_uuid):
        parent_uuid = ''

    context = {
        'request': request,
        'config': config,
        'user': user,
        'url': request.url_for('search'),
        'parent_uuid': parent_uuid,
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse('upload.html', context)


@router.get('/upload_complete/{uuid}')
async def upload_complete(
        request: Request,
        uuid: str,
        user: domain.User = Depends(dep.get_current_user),
):
    """Page that advises user to wait after upload."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'uuid': uuid,
        'url': request.url_for('search'),
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse('upload_complete.html', context)


@router.post('/upload')
async def upload_post(
        request: Request,
        item_uuid: str = Form(...),
        tags: str = Form(default=''),
        collection: str = Form(default=''),
        user: domain.User = Depends(dep.get_current_user),
        files: list[UploadFile] = File(...),
        use_case: use_cases.UploadUseCase = Depends(
            dep.get_upload_use_case,
        ),
):
    """Upload media page."""
    if user.is_anon():  # TODO - move it to a separate decorator
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect login or password',
            headers={'WWW-Authenticate': 'Basic realm="omoide"'},
        )

    is_collection = bool(collection)

    something_wrong_with_files = not files  # FIXME
    if something_wrong_with_files:
        details = infra.parse.details_from_params(
            params=request.query_params,
            items_per_page=constants.ITEMS_PER_PAGE,
        )

        query = infra.query_maker.from_request(request.query_params)

        context = {
            'request': request,
            'config': config,
            'user': user,
            'url': request.url_for('search'),
            'query': infra.query_maker.QueryWrapper(query, details),
        }

        return dep.templates.TemplateResponse('upload.html', context)

    access, uuids = await use_case.execute(
        user=user,
        item_uuid=UUID(item_uuid),
        is_collection=is_collection,
        files=files,
        tags=list(filter(None, tags.split('\n'))),  # FIXME
        permissions=[],  # FIXME
        features=[],  # FIXME
    )

    if access.does_not_exist or access.is_not_given:
        raise fastapi.HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Given item does not exist',
        )

    url = request.url_for('upload_complete', uuid=item_uuid)
    return fastapi.responses.RedirectResponse(
        url,
        status_code=status.HTTP_302_FOUND,
    )
