# -*- coding: utf-8 -*-
"""EXIF related API operations.
"""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

import omoide.domain.models
from omoide import use_cases
from omoide.application import app_models
from omoide.domain import models
from omoide.domain.interfaces.in_infra import in_policy
from omoide.domain.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web

router = APIRouter(prefix='/api/exif')


@router.post('/{item_uuid}')
async def api_create_exif(
        item_uuid: UUID,
        raw_exif: app_models.RawEXIF,
        user: models.User = Depends(dep.get_current_user),
        policy: in_policy.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.CreateEXIFUseCase = Depends(
            dep.create_exif_use_case),
):
    """Create."""
    exif = models.EXIF(item_uuid=item_uuid, exif=raw_exif.exif)
    result = await use_case.execute(policy, user, exif)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return web.serialize(result.value)


@router.get('/{item_uuid}')
async def api_read_exif(
        item_uuid: UUID,
        user: models.User = Depends(dep.get_current_user),
        policy: in_policy.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ReadEXIFUseCase = Depends(
            dep.read_exif_use_case),
):
    """Read."""
    result = await use_case.execute(policy, user, item_uuid)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return web.serialize(result.value)


@router.get('/{item_uuid}')
async def api_update_exif(
        item_uuid: UUID,
        raw_exif: app_models.RawEXIF,
        user: models.User = Depends(dep.get_current_user),
        policy: in_policy.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.UpdateEXIFUseCase = Depends(
            dep.update_exif_use_case),
):
    """Update."""
    exif = models.EXIF(item_uuid=item_uuid, exif=raw_exif.exif)
    result = await use_case.execute(policy, user, exif)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return web.serialize(result.value)


@router.delete('/{item_uuid}')
async def api_delete_exif(
        item_uuid: UUID,
        user: omoide.domain.models.User = Depends(dep.get_current_user),
        policy: in_policy.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.DeleteEXIFUseCase = Depends(
            dep.delete_exif_use_case),
):
    """Delete."""
    result = await use_case.execute(policy, user, item_uuid)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return web.serialize(result.value)
