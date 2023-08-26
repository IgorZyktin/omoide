"""Metainfo related API operations.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from omoide import use_cases
from omoide.application import web
from omoide.domain.application import app_constants
from omoide.domain.application import input_models
from omoide.domain.core import core_models
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/metainfo')


@router.put('/{item_uuid}')
async def api_update_metainfo(
        item_uuid: UUID,
        in_metainfo: input_models.InMetainfo,
        user: Annotated[core_models.User, Depends(dep.get_current_user)],
        use_case: Annotated[use_cases.UpdateMetainfoUseCase,
                            Depends(dep.update_metainfo_use_case)],
):
    """Update metainfo entry."""
    metainfo = core_models.Metainfo(
        item_uuid=item_uuid,
        created_at=app_constants.DUMMY_TIME,
        updated_at=app_constants.DUMMY_TIME,
        deleted_at=None,
        user_time=in_metainfo.user_time,
        content_type=in_metainfo.content_type,
        author=in_metainfo.author,
        author_url=in_metainfo.author_url,
        saved_from_url=in_metainfo.saved_from_url,
        description=in_metainfo.description,
        extras=in_metainfo.extras or {},
        content_size=in_metainfo.content_size,
        preview_size=in_metainfo.preview_size,
        thumbnail_size=in_metainfo.thumbnail_size,
        content_width=in_metainfo.content_width,
        content_height=in_metainfo.content_height,
        preview_width=in_metainfo.preview_width,
        preview_height=in_metainfo.preview_height,
        thumbnail_width=in_metainfo.thumbnail_width,
        thumbnail_height=in_metainfo.thumbnail_height,
    )

    await web.run(use_case.execute, user, item_uuid, metainfo)
    return {}


@router.get('/{item_uuid}')
async def api_read_metainfo(
        item_uuid: UUID,
        user: Annotated[core_models.User, Depends(dep.get_current_user)],
        use_case: Annotated[use_cases.ReadMetainfoUseCase,
                            Depends(dep.read_metainfo_use_case)],
):
    """Get metainfo."""
    result = await web.run(use_case.execute, user, item_uuid)
    return result
