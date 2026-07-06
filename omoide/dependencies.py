"""Dependencies."""

import functools
from typing import Annotated

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPBasic
from fastapi.security import HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
import jinja2
import nano_settings as ns
import python_utilz as pu
from starlette.requests import Request

from omoide import cfg
from omoide import const
from omoide import infra
from omoide import localization
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.implementations import impl_sqlalchemy
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.infra.interfaces import AbsAuthenticator
from omoide.infra.locators import WebLocator
from omoide.object_storage import interfaces as object_interfaces
from omoide.object_storage.implementations.pgl_object_storage import PgLargeObjectStorage
from omoide.omoide_app.auth.auth_use_cases import LoginUserUseCase
from omoide.presentation import web


@functools.cache
def get_config() -> cfg.Config:
    """Get config instance."""
    return ns.from_env(cfg.Config, env_prefix='omoide_app')


@functools.cache
def get_database() -> impl_sqlalchemy.SqlalchemyDatabase:
    """Get database instance."""
    config = get_config()
    return impl_sqlalchemy.SqlalchemyDatabase(
        db_url=config.db_url.get_secret_value(),
        echo=False,
    )


# application specific objects ------------------------------------------------


def get_aim(request: Request) -> web.AimWrapper:
    """General way of getting aim."""
    params = dict(request.query_params)
    return web.AimWrapper.from_params(
        params=params,
        items_per_page=25,
    )


_optional_basic = HTTPBasic(auto_error=False)


async def get_credentials(request: Request) -> HTTPBasicCredentials | None:
    """Extract Basic-Auth credentials without triggering a login dialog.

    The login challenge (401 + ``WWW-Authenticate``) lives only on
    ``/login``, where ``auth_controllers.security`` uses ``HTTPBasic``
    with ``auto_error=True``. Everywhere else we silently fall back to
    anon — any failure mode (no header, wrong scheme, bad base64,
    missing colon) maps to ``None``. ``HTTPBasic(auto_error=False)``
    handles "no header" itself; the inner ``try`` covers the malformed
    cases, which the base class still raises on.
    """
    try:
        return await _optional_basic(request)
    except HTTPException:
        return None


def get_authenticator() -> AbsAuthenticator:
    """Get authenticator instance."""
    return infra.BcryptAuthenticator()


@functools.cache
def get_object_storage(
    database: Annotated[impl_sqlalchemy.SqlalchemyDatabase, Depends(get_database)],
) -> object_interfaces.AbsObjectStorage:
    """Get long-term object storage.

    Swap this factory's return value to switch the backend (e.g. an S3
    implementation) — the controller / use case only depend on the
    ``AbsObjectStorage`` interface.
    """
    return PgLargeObjectStorage(database=database)


def get_users_repo() -> db_interfaces.AbsUsersRepo:
    """Get repo instance."""
    return impl_sqlalchemy.UsersRepo()


def get_items_repo() -> db_interfaces.AbsItemsRepo:
    """Get repo instance."""
    return impl_sqlalchemy.ItemsRepo()


def get_exif_repo() -> db_interfaces.AbsEXIFRepo:
    """Get repo instance."""
    return impl_sqlalchemy.EXIFRepo()


def get_meta_repo() -> db_interfaces.AbsMetaRepo:
    """Get repo instance."""
    return impl_sqlalchemy.MetaRepo()


def get_misc_repo() -> db_interfaces.AbsMiscRepo:
    """Get repo instance."""
    return impl_sqlalchemy.MiscRepo()


def get_browse_repo() -> db_interfaces.AbsBrowseRepo:
    """Get repo instance."""
    return impl_sqlalchemy.BrowseRepo()


def get_search_repo() -> db_interfaces.AbsSearchRepo:
    """Get repo instance."""
    return impl_sqlalchemy.SearchRepo()


def get_tags_repo() -> db_interfaces.AbsTagsRepo:
    """Get repo instance."""
    return impl_sqlalchemy.TagsRepo()


def get_signatures_repo() -> db_interfaces.AbsSignaturesRepo:
    """Get repo instance."""
    return impl_sqlalchemy.SignaturesRepo()


def get_commands_repo() -> db_interfaces.AbsCommandsRepo:
    """Get repo instance."""
    return impl_sqlalchemy.CommandsRepo()


async def get_current_user(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(get_credentials)],
    authenticator: Annotated[AbsAuthenticator, Depends(get_authenticator)],
    database: Annotated[AbsDatabase, Depends(get_database)],
    users_repo: Annotated[db_interfaces.AbsUsersRepo, Depends(get_users_repo)],
) -> models.User:
    """Return current user or create anon."""
    if credentials is None:
        return models.User.new_anon()
    use_case = LoginUserUseCase(authenticator, database, users_repo)
    return await use_case.execute(credentials.username, credentials.password)


async def get_known_user(
    current_user: Annotated[models.User, Depends(get_current_user)],
) -> models.User:
    """Return current user, raise if user is anon."""
    if current_user.is_not_anon:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail='You must be registered to do this',
    )


async def get_admin_user(
    current_user: Annotated[models.User, Depends(get_current_user)],
) -> models.User:
    """Return admin user, raise if user is not one."""
    if current_user.is_admin:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail='You must be registered to do this',
    )


@functools.cache
def get_templates() -> Jinja2Templates:
    """Get templates instance."""
    templates = Jinja2Templates(directory='omoide/presentation/templates')
    templates.env.globals['zip'] = zip
    templates.env.globals['version'] = str(const.FRONTEND_VERSION)

    config = get_config()
    locator = WebLocator(root='content', prefix_size=config.prefix_size)
    templates.env.globals['get_video_url'] = locator.get_video_location
    templates.env.globals['get_content_url'] = locator.get_content_location
    templates.env.globals['get_preview_url'] = locator.get_preview_location
    templates.env.globals['get_thumbnail_url'] = locator.get_thumbnail_location

    templates.env.globals['human_readable_size'] = pu.human_readable_size
    templates.env.globals['sep_digits'] = pu.sep_digits
    templates.env.globals['Status'] = models.Status

    @jinja2.pass_context
    def translate(context: jinja2.runtime.Context, text: str) -> str:
        user = context.get('user')
        if user is None:
            return text
        return localization.gettext(text, user=user)

    templates.env.globals['_'] = translate
    return templates
