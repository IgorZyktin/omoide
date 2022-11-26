# -*- coding: utf-8 -*-
"""External components.
"""
import binascii
from base64 import b64decode
from typing import Optional

from databases import Database
from fastapi import Depends
from fastapi.security import HTTPBasicCredentials
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from omoide import infra
from omoide import use_cases
from omoide.domain import auth
from omoide.domain import interfaces
from omoide.presentation import app_config
from omoide.presentation import constants
from omoide.presentation import web
from omoide.storage.repositories import asyncpg

_config = app_config.init()
db = Database(_config.db_url.get_secret_value())

search_repository = asyncpg.SearchRepository(db)
preview_repository = asyncpg.PreviewRepository(db)
browse_repository = asyncpg.BrowseRepository(db)

users_repository = asyncpg.UsersRepository(db)
users_read_repository = asyncpg.UsersReadRepository(db)

items_read_repository = asyncpg.ItemsReadRepository(db)
items_write_repository = asyncpg.ItemsWriteRepository(db)

media_repository = asyncpg.MediaRepository(db)
exif_repository = asyncpg.EXIFRepository(db)
metainfo_repository = asyncpg.MetainfoRepository(db)

templates = Jinja2Templates(directory='omoide/presentation/templates')


def get_aim(
        request: Request,
) -> web.AimWrapper:
    """General way of getting aim."""
    params = dict(request.query_params)
    return web.AimWrapper.from_params(
        params=params,
        items_per_page=min(constants.ITEMS_PER_PAGE,
                           constants.MAX_ITEMS_PER_PAGE),
    )


def get_credentials(
        request: Request,
) -> HTTPBasicCredentials:
    """Try extraction credentials from user request, but not trigger login."""
    authorization: Optional[str] = request.headers.get('Authorization')
    anon = HTTPBasicCredentials(username='', password='')

    if authorization:
        scheme, _, param = authorization.partition(' ')

        if scheme.lower() == 'basic':
            try:
                data = b64decode(param).decode('ascii')
            except (ValueError, UnicodeDecodeError, binascii.Error):
                return anon

            username, separator, password = data.partition(':')

            if not separator:
                return anon

            return HTTPBasicCredentials(username=username, password=password)

    return anon


def config() -> app_config.Config:
    """Get config instance."""
    return app_config.get_config()


def get_auth_use_case() -> use_cases.AuthUseCase:
    """Get use case instance."""
    return use_cases.AuthUseCase(
        users_repo=users_read_repository,
    )


def get_authenticator() -> interfaces.AbsAuthenticator:
    """Get authenticator instance."""
    return infra.BcryptAuthenticator(
        complexity=4,  # minimal
    )


def get_policy() -> interfaces.AbsPolicy:
    """Get policy instance."""
    return infra.Policy(
        items_repo=items_read_repository,
    )


async def get_current_user(
        credentials: HTTPBasicCredentials = Depends(get_credentials),
        use_case: use_cases.AuthUseCase = Depends(get_auth_use_case),
        authenticator: interfaces.AbsAuthenticator = Depends(get_authenticator)
) -> auth.User:
    """Load current user or use anon user."""
    if not credentials.username or not credentials.password:
        return auth.User.new_anon()
    return await use_case.execute(credentials, authenticator)


# application related use cases -----------------------------------------------


def app_dynamic_search_use_case() -> use_cases.AppDynamicSearchUseCase:
    """Get use case instance."""
    return use_cases.AppDynamicSearchUseCase(
        search_repo=search_repository,
    )


def app_paged_search_use_case() -> use_cases.AppPagedSearchUseCase:
    """Get use case instance."""
    return use_cases.AppPagedSearchUseCase(
        search_repo=search_repository,
    )


def app_preview_use_case() -> use_cases.AppPreviewUseCase:
    """Get use case instance."""
    return use_cases.AppPreviewUseCase(
        preview_repo=preview_repository,
        users_repo=users_read_repository,
        items_repo=items_read_repository,
    )


def app_browse_use_case() -> use_cases.AppBrowseUseCase:
    """Get use case instance."""
    return use_cases.AppBrowseUseCase(
        browse_repo=browse_repository,
        users_repo=users_read_repository,
        items_repo=items_read_repository,
    )


def app_home_use_case() -> use_cases.AppHomeUseCase:
    """Get use case instance."""
    return use_cases.AppHomeUseCase(
        browse_repo=browse_repository,
    )


def app_upload_use_case() -> use_cases.AppUploadUseCase:
    """Get use case instance."""
    return use_cases.AppUploadUseCase(
        items_repo=items_read_repository,
        users_repo=users_read_repository,
    )


# app item related use cases --------------------------------------------------


def api_search_use_case() -> use_cases.ApiSearchUseCase:
    """Get use case instance."""
    return use_cases.ApiSearchUseCase(
        search_repo=search_repository,
    )


def app_item_create_use_case() -> use_cases.AppItemCreateUseCase:
    """Get use case instance."""
    return use_cases.AppItemCreateUseCase(
        items_repo=items_write_repository,
        users_repo=users_read_repository,
    )


def app_item_update_use_case() -> use_cases.AppItemUpdateUseCase:
    """Get use case instance."""
    return use_cases.AppItemUpdateUseCase(
        items_repo=items_write_repository,
        users_repo=users_read_repository,
    )


def app_item_delete_use_case() -> use_cases.AppItemDeleteUseCase:
    """Get use case instance."""
    return use_cases.AppItemDeleteUseCase(
        items_repo=items_write_repository,
    )


# api item related use cases --------------------------------------------------


def api_item_create_use_case() -> use_cases.ApiItemCreateUseCase:
    """Get use case instance."""
    return use_cases.ApiItemCreateUseCase(
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


def api_item_read_use_case() -> use_cases.ApiItemReadUseCase:
    """Get use case instance."""
    return use_cases.ApiItemReadUseCase(
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


# TODO: remove this
def update_item_use_case() -> use_cases.UpdateItemUseCase:
    """Get use case instance."""
    return use_cases.UpdateItemUseCase(
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


def api_item_copy_thumbnail_use_case() -> use_cases.ApiCopyThumbnailUseCase:
    """Get use case instance."""
    return use_cases.ApiCopyThumbnailUseCase(
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
        media_repo=media_repository,
    )


def api_item_alter_parent_use_case() -> use_cases.ApiItemAlterParentUseCase:
    """Get use case instance."""
    return use_cases.ApiItemAlterParentUseCase(
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
        media_repo=media_repository,
    )


def api_item_alter_tags_use_case() -> use_cases.ApiItemAlterTagsUseCase:
    """Get use case instance."""
    return use_cases.ApiItemAlterTagsUseCase(
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


def api_item_alter_permissions_use_case() \
        -> use_cases.ApiItemAlterPermissionsUseCase:
    """Get use case instance."""
    return use_cases.ApiItemAlterPermissionsUseCase(
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


# api related use cases -------------------------------------------------------

def api_browse_use_case() -> use_cases.APIBrowseUseCase:
    """Get use case instance."""
    return use_cases.APIBrowseUseCase(
        browse_repo=browse_repository,
    )


# api item related use cases --------------------------------------------------

def api_item_delete_use_case() -> use_cases.ApiItemDeleteUseCase:
    """Get use case instance."""
    return use_cases.ApiItemDeleteUseCase(
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


# api media related use cases -------------------------------------------------


def read_media_use_case() -> use_cases.ReadMediaUseCase:
    """Get use case instance."""
    return use_cases.ReadMediaUseCase(media_repository)


def update_media_use_case() -> use_cases.CreateOrUpdateMediaUseCase:
    """Get use case instance."""
    return use_cases.CreateOrUpdateMediaUseCase(media_repository)


def delete_media_use_case() -> use_cases.DeleteMediaUseCase:
    """Get use case instance."""
    return use_cases.DeleteMediaUseCase(media_repository)


# api exif related use cases -------------------------------------------------


def read_exif_use_case() -> use_cases.ReadEXIFUseCase:
    """Get use case instance."""
    return use_cases.ReadEXIFUseCase(exif_repository)


def update_exif_use_case() -> use_cases.CreateOrUpdateEXIFUseCase:
    """Get use case instance."""
    return use_cases.CreateOrUpdateEXIFUseCase(exif_repository)


def delete_exif_use_case() -> use_cases.DeleteEXIFUseCase:
    """Get use case instance."""
    return use_cases.DeleteEXIFUseCase(exif_repository)


# api metainfo related use cases ----------------------------------------------


def read_metainfo_use_case() -> use_cases.ReadMetainfoUseCase:
    """Get use case instance."""
    return use_cases.ReadMetainfoUseCase(metainfo_repository)


def update_metainfo_use_case() -> use_cases.UpdateMetainfoUseCase:
    """Get use case instance."""
    return use_cases.UpdateMetainfoUseCase(metainfo_repository)


# app profile related use cases -----------------------------------------------
def profile_quotas_use_case() -> use_cases.AppProfileQuotasUseCase:
    """Get use case instance."""
    return use_cases.AppProfileQuotasUseCase(
        users_repo=users_read_repository,
        items_repo=items_read_repository,
    )
