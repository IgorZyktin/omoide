# -*- coding: utf-8 -*-
"""EXIF related API operations.
"""
import http
from uuid import UUID

from fastapi import HTTPException, Depends, APIRouter

from omoide import domain, use_cases
from omoide.domain import exceptions
from omoide.presentation import api_models
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/exif')


@router.put('/{uuid}')
async def api_create_or_update_exif(
        uuid: UUID,
        exif_in: api_models.EXIFIn,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.CreateOrUpdateEXIFUseCase = Depends(
            dep.update_exif_use_case),
):
    """Create or update EXIF entry."""
    try:
        await use_case.execute(user, uuid, exif_in)
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    return 'ok'


@router.get('/{uuid}')
async def api_read_exif(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.ReadEXIFUseCase = Depends(
            dep.read_exif_use_case),
):
    """Get EXIF."""
    try:
        exif = await use_case.execute(user, uuid)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    return exif.dict()


@router.delete('/{uuid}')
async def api_delete_exif(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.DeleteEXIFUseCase = Depends(
            dep.delete_exif_use_case),
):
    """Delete EXIF."""
    try:
        await use_case.execute(user, uuid)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    return 'ok'
