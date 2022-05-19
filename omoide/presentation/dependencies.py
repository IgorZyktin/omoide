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
from omoide.presentation.config import config
from omoide.storage import repositories

db = Database(config.omoide_db_url)
current_authenticator = infra.BcryptAuthenticator(complexity=4)  # minimal

search_repository = repositories.SearchRepository(db)
search_use_case = use_cases.SearchUseCase(search_repository)

preview_repository = repositories.PreviewRepository(db)
preview_use_case = use_cases.PreviewUseCase(preview_repository)

browse_repository = repositories.BrowseRepository(db)
browse_use_case = use_cases.BrowseUseCase(browse_repository)

base_repository = repositories.BaseRepository(db)
auth_use_case = use_cases.AuthUseCase(base_repository)

item_crud_repository = repositories.ItemCRUDRepository(db)
_create_item_use_case = use_cases.CreateItemUseCase(item_crud_repository)
upload_use_case = use_cases.UploadUseCase(item_crud_repository)

home_repository = repositories.HomeRepository(db)
home_use_case = use_cases.HomeUseCase(home_repository)

items_repository = repositories.ItemsRepository(db)

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


def get_search_use_case():
    """Get use case instance."""
    return search_use_case


def get_preview_use_case():
    """Get use case instance."""
    return preview_use_case


def get_browse_use_case():
    """Get use case instance."""
    return browse_use_case


def get_home_use_case():
    """Get use case instance."""
    return home_use_case


def get_create_item_use_case():
    """Get use case instance."""
    return _create_item_use_case


def get_upload_use_case() -> use_cases.UploadUseCase:
    """Get use case instance."""
    return upload_use_case


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
