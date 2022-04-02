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
from omoide.presentation.config import config
from omoide.storage import repositories

db = Database(config.omoide_db_url)

search_repository = repositories.SearchRepository(db)
search_use_case = use_cases.SearchUseCase(search_repository)

preview_repository = repositories.PreviewRepository(db)
preview_use_case = use_cases.PreviewUseCase(preview_repository)

browse_repository = repositories.BrowseRepository(db)
browse_use_case = use_cases.BrowseUseCase(browse_repository)

by_user_repository = repositories.ByUserRepository(db)
by_user_use_case = use_cases.ByUserUseCase(by_user_repository)

base_repository = repositories.BaseRepository(db)
auth_use_case = use_cases.AuthUseCase(base_repository)

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


async def get_current_user(
        credentials: HTTPBasicCredentials = fastapi.Depends(get_credentials),
        use_case: use_cases.AuthUseCase = fastapi.Depends(get_auth_use_case),
) -> auth.User:
    """Load current user or use anon user."""
    if not credentials.username or not credentials.password:
        return auth.User.new_anon()
    return await use_case.execute(credentials)


def get_search_use_case():
    """Get use case instance."""
    return search_use_case


def get_preview_use_case():
    """Get use case instance."""
    return preview_use_case


def get_browse_use_case():
    """Get use case instance."""
    return browse_use_case


def get_by_user_use_case():
    """Get use case instance."""
    return by_user_use_case
