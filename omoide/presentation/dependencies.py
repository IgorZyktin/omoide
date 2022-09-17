# -*- coding: utf-8 -*-
"""External components.
"""
import binascii
from base64 import b64decode

import fastapi
from databases import Database
from fastapi.security import HTTPBasicCredentials
from starlette.templating import Jinja2Templates

from omoide import infra
from omoide import use_cases
from omoide.domain import auth
from omoide.domain import interfaces
from omoide.presentation import app_config
from omoide.storage import repositories

config = app_config.init()
db = Database(config.db_url.get_secret_value())
current_authenticator = infra.BcryptAuthenticator(complexity=4)  # minimal

search_repository = repositories.SearchRepository(db)
search_use_case = use_cases.SearchUseCase(search_repository)

preview_repository = repositories.PreviewRepository(db)

browse_repository = repositories.BrowseRepository(db)

base_repository = repositories.BaseRepository(db)
auth_use_case = use_cases.AuthUseCase(base_repository)

users_repository = repositories.UsersRepository(db)
items_repository = repositories.ItemsRepository(db)
media_repository = repositories.MediaRepository(db)
exif_repository = repositories.EXIFRepository(db)
meta_repository = repositories.MetaRepository(db)

current_policy = infra.Policy(
    items_repo=items_repository,
)

templates = Jinja2Templates(directory='omoide/presentation/templates')


def get_credentials(
        request: fastapi.Request,
) -> HTTPBasicCredentials:
    """Try extraction credentials from user request, but not trigger login."""
    authorization: str = request.headers.get('Authorization')
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


def get_auth_use_case():
    """Get use case instance."""
    return auth_use_case


def get_authenticator():
    """Get authenticator instance."""
    return current_authenticator


def get_policy():
    """Get policy instance."""
    return current_policy


async def get_current_user(
        credentials: HTTPBasicCredentials = fastapi.Depends(get_credentials),
        use_case: use_cases.AuthUseCase = fastapi.Depends(get_auth_use_case),
        authenticator: interfaces.AbsAuthenticator = fastapi.Depends(
            get_authenticator,
        ),
        active_config: app_config.Config = fastapi.Depends(config),
) -> auth.User:
    """Load current user or use anon user."""
    if not credentials.username or not credentials.password:
        return auth.User.new_anon()
    return await use_case.execute(
        credentials,
        authenticator,
        env=active_config.env,
        test_users=active_config.test_users,
    )


# application related use cases -----------------------------------------------


def get_search_use_case():
    """Get use case instance."""
    return search_use_case


def app_preview_use_case() -> use_cases.PreviewUseCase:
    """Get use case instance."""
    return use_cases.PreviewUseCase(preview_repository)


def app_browse_use_case() -> use_cases.AppBrowseUseCase:
    """Get use case instance."""
    return use_cases.AppBrowseUseCase(browse_repository)


def app_home_use_case() -> use_cases.HomeUseCase:
    """Get use case instance."""
    return use_cases.HomeUseCase(items_repository)


# app item related use cases --------------------------------------------------

def app_item_update_use_case() -> use_cases.AppItemUpdateUseCase:
    """Get use case instance."""
    return use_cases.AppItemUpdateUseCase(items_repository, users_repository)


def app_item_delete_use_case() -> use_cases.AppItemDeleteUseCase:
    """Get use case instance."""
    return use_cases.AppItemDeleteUseCase(items_repository)


# api item related use cases --------------------------------------------------


def api_item_create_use_case() -> use_cases.ApiItemCreateUseCase:
    """Get use case instance."""
    return use_cases.ApiItemCreateUseCase(items_repository)


def api_item_read_use_case() -> use_cases.ApiItemReadUseCase:
    """Get use case instance."""
    return use_cases.ApiItemReadUseCase(items_repository)


# TODO: remove this
def update_item_use_case() -> use_cases.UpdateItemUseCase:
    """Get use case instance."""
    return use_cases.UpdateItemUseCase(items_repository)


def api_item_alter_parent_use_case() -> use_cases.ApiItemAlterParentUseCase:
    """Get use case instance."""
    return use_cases.ApiItemAlterParentUseCase(items_repository)


def api_item_alter_tags_use_case() -> use_cases.ApiItemAlterTagsUseCase:
    """Get use case instance."""
    return use_cases.ApiItemAlterTagsUseCase(items_repository)


def api_item_alter_permissions_use_case()\
        -> use_cases.ApiItemAlterPermissionsUseCase:
    """Get use case instance."""
    return use_cases.ApiItemAlterPermissionsUseCase(items_repository)


# api related use cases -------------------------------------------------------

def api_browse_use_case() -> use_cases.APIBrowseUseCase:
    """Get use case instance."""
    return use_cases.APIBrowseUseCase(items_repository)


# api item related use cases --------------------------------------------------

def api_item_delete_use_case() -> use_cases.ApiItemDeleteUseCase:
    """Get use case instance."""
    return use_cases.ApiItemDeleteUseCase(items_repository)


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


# api meta related use cases -------------------------------------------------


def read_meta_use_case() -> use_cases.ReadMetaUseCase:
    """Get use case instance."""
    return use_cases.ReadMetaUseCase(items_repository, meta_repository)


def update_meta_use_case() -> use_cases.CreateOrUpdateMetaUseCase:
    """Get use case instance."""
    return use_cases.CreateOrUpdateMetaUseCase(items_repository,
                                               meta_repository)
