# -*- coding: utf-8 -*-
"""External components.
"""
from databases import Database
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

templates = Jinja2Templates(directory='presentation/templates')


def get_current_user():
    """Load current user or use anon user."""
    return auth.User(
        uuid='',
        login='anon',
        password='',
        name='anon',
        visibility=None,
        language=None,
        last_seen=None,
    )


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
