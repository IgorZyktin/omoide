# -*- coding: utf-8 -*-
"""External components.
"""
import binascii
from base64 import b64decode

import fastapi
from databases import Database
from fastapi.security import HTTPBasicCredentials
from starlette.templating import Jinja2Templates

from omoide import use_cases
from omoide.domain import auth
from omoide.domain import interfaces
from omoide.presentation import infra
from omoide.presentation import app_config
from omoide.storage import repositories

config = app_config.init()
db = Database(config.db_url)
current_authenticator = infra.BcryptAuthenticator(complexity=4)  # minimal

search_repository = repositories.SearchRepository(db)
search_use_case = use_cases.SearchUseCase(search_repository)

preview_repository = repositories.PreviewRepository(db)

browse_repository = repositories.BrowseRepository(db)

base_repository = repositories.BaseRepository(db)
auth_use_case = use_cases.AuthUseCase(base_repository)

upload_repository = repositories.UploadRepository(db)
items_repository = repositories.ItemsRepository(db)
media_repository = repositories.MediaRepository(db)

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


async def get_current_user(
        credentials: HTTPBasicCredentials = fastapi.Depends(get_credentials),
        use_case: use_cases.AuthUseCase = fastapi.Depends(get_auth_use_case),
        authenticator: interfaces.AbsAuthenticator = fastapi.Depends(
            get_authenticator,
        ),
) -> auth.User:
    """Load current user or use anon user."""
    if not credentials.username or not credentials.password:
        return auth.User.new_anon()
    return await use_case.execute(credentials, authenticator)


# application related use cases -----------------------------------------------


def app_delete_item_use_case() -> use_cases.AppDeleteItemUseCase:
    """Get use case instance."""
    return use_cases.AppDeleteItemUseCase(items_repository)


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


def app_upload_use_case() -> use_cases.UploadUseCase:
    """Get use case instance."""
    return use_cases.UploadUseCase(upload_repository)


# api item related use cases --------------------------------------------------


def create_item_use_case() -> use_cases.CreateItemUseCase:
    """Get use case instance."""
    return use_cases.CreateItemUseCase(items_repository)


def read_item_use_case() -> use_cases.ReadItemUseCase:
    """Get use case instance."""
    return use_cases.ReadItemUseCase(items_repository)


def update_item_use_case() -> use_cases.UpdateItemUseCase:
    """Get use case instance."""
    return use_cases.UpdateItemUseCase(items_repository)


def delete_item_use_case() -> use_cases.DeleteItemUseCase:
    """Get use case instance."""
    return use_cases.DeleteItemUseCase(items_repository)


def api_browse_use_case() -> use_cases.APIBrowseUseCase:
    """Get use case instance."""
    return use_cases.APIBrowseUseCase(items_repository)


# api media related use cases -------------------------------------------------


def read_media_use_case() -> use_cases.ReadMediaUseCase:
    """Get use case instance."""
    return use_cases.ReadMediaUseCase(items_repository, media_repository)


def update_media_use_case() -> use_cases.CreateOrUpdateMediaUseCase:
    """Get use case instance."""
    return use_cases.CreateOrUpdateMediaUseCase(items_repository,
                                                media_repository)


def delete_media_use_case() -> use_cases.DeleteMediaUseCase:
    """Get use case instance."""
    return use_cases.DeleteMediaUseCase(items_repository, media_repository)
