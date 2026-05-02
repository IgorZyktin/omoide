"""Dependencies."""

from base64 import b64decode
import binascii
import functools
from typing import Annotated

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
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
from omoide.infra import mediators
from omoide.infra.interfaces import AbsAuthenticator
from omoide.infra.web_locator import WebLocator
from omoide.object_storage import interfaces as object_interfaces
from omoide.object_storage.implementations.file_server import FileObjectStorageServer
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


def get_credentials(request: Request) -> HTTPBasicCredentials:
    """Extract credentials from user request, but do not trigger login."""
    authorization: str | None = request.headers.get('Authorization')
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


def get_authenticator() -> AbsAuthenticator:
    """Get authenticator instance."""
    return infra.BcryptAuthenticator()


@functools.cache
def get_object_storage(
    database: Annotated[AbsDatabase, Depends(get_database)],
) -> object_interfaces.AbsObjectStorage:
    """Get policy instance."""
    config = get_config()
    return FileObjectStorageServer(
        database=database,
        media=impl_sqlalchemy.MediaRepo(),
        misc=impl_sqlalchemy.MiscRepo(),
        prefix_size=config.prefix_size,
    )


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


@functools.cache
def get_mediator(
    authenticator: Annotated[AbsAuthenticator, Depends(get_authenticator)],
    object_storage: Annotated[object_interfaces.AbsObjectStorage, Depends(get_object_storage)],
    database: Annotated[AbsDatabase, Depends(get_database)],
) -> mediators.Mediator:
    """Get mediator instance."""
    return mediators.Mediator(
        authenticator=authenticator,
        database=database,
        browse=impl_sqlalchemy.BrowseRepo(),
        exif=impl_sqlalchemy.EXIFRepo(),
        items=impl_sqlalchemy.ItemsRepo(),
        meta=impl_sqlalchemy.MetaRepo(),
        misc=impl_sqlalchemy.MiscRepo(),
        search=impl_sqlalchemy.SearchRepo(),
        signatures=impl_sqlalchemy.SignaturesRepo(),
        tags=impl_sqlalchemy.TagsRepo(),
        users=impl_sqlalchemy.UsersRepo(),
        object_storage=object_storage,
    )


def get_exif_mediator(
    authenticator: Annotated[AbsAuthenticator, Depends(get_authenticator)],
    database: Annotated[AbsDatabase, Depends(get_database)],
) -> mediators.EXIFMediator:
    """Get mediator instance."""
    return mediators.EXIFMediator(
        authenticator=authenticator,
        database=database,
        exif=impl_sqlalchemy.EXIFRepo(),
        items=impl_sqlalchemy.ItemsRepo(),
    )


def get_metainfo_mediator(
    authenticator: Annotated[AbsAuthenticator, Depends(get_authenticator)],
    database: Annotated[AbsDatabase, Depends(get_database)],
) -> mediators.EXIFMediator:
    """Get mediator instance."""
    return mediators.EXIFMediator(
        authenticator=authenticator,
        database=database,
        exif=impl_sqlalchemy.EXIFRepo(),
        items=impl_sqlalchemy.ItemsRepo(),
    )


def get_search_mediator(
    database: Annotated[AbsDatabase, Depends(get_database)],
) -> mediators.SearchMediator:
    """Get mediator instance."""
    return mediators.SearchMediator(
        browse=impl_sqlalchemy.BrowseRepo(),
        database=database,
        search=impl_sqlalchemy.SearchRepo(),
        tags=impl_sqlalchemy.TagsRepo(),
        users=impl_sqlalchemy.UsersRepo(),
    )


def get_home_mediator(
    database: Annotated[AbsDatabase, Depends(get_database)],
) -> mediators.HomeMediator:
    """Get mediator instance."""
    return mediators.HomeMediator(
        database=database,
        search=impl_sqlalchemy.SearchRepo(),
        users=impl_sqlalchemy.UsersRepo(),
    )


def get_browse_mediator(
    database: Annotated[AbsDatabase, Depends(get_database)],
) -> mediators.BrowseMediator:
    """Get mediator instance."""
    return mediators.BrowseMediator(
        browse=impl_sqlalchemy.BrowseRepo(),
        database=database,
        items=impl_sqlalchemy.ItemsRepo(),
        search=impl_sqlalchemy.SearchRepo(),
        users=impl_sqlalchemy.UsersRepo(),
    )


def get_users_mediator(
    authenticator: Annotated[AbsAuthenticator, Depends(get_authenticator)],
    database: Annotated[AbsDatabase, Depends(get_database)],
) -> mediators.UsersMediator:
    """Get mediator instance."""
    return mediators.UsersMediator(
        authenticator=authenticator,
        database=database,
        items=impl_sqlalchemy.ItemsRepo(),
        meta=impl_sqlalchemy.MetaRepo(),
        misc=impl_sqlalchemy.MiscRepo(),
        tags=impl_sqlalchemy.TagsRepo(),
        users=impl_sqlalchemy.UsersRepo(),
    )


def get_items_mediator(
    authenticator: Annotated[AbsAuthenticator, Depends(get_authenticator)],
    database: Annotated[AbsDatabase, Depends(get_database)],
    object_storage: Annotated[object_interfaces.AbsObjectStorage, Depends(get_object_storage)],
) -> mediators.ItemsMediator:
    """Get mediator instance."""
    return mediators.ItemsMediator(
        authenticator=authenticator,
        database=database,
        items=impl_sqlalchemy.ItemsRepo(),
        meta=impl_sqlalchemy.MetaRepo(),
        misc=impl_sqlalchemy.MiscRepo(),
        object_storage=object_storage,
        signatures=impl_sqlalchemy.SignaturesRepo(),
        tags=impl_sqlalchemy.TagsRepo(),
        users=impl_sqlalchemy.UsersRepo(),
    )


async def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(get_credentials)],
    mediator: Annotated[mediators.UsersMediator, Depends(get_users_mediator)],
) -> models.User:
    """Return current user or create anon."""
    use_case = LoginUserUseCase(mediator)
    if not credentials.username or not credentials.password:
        return models.User.new_anon()
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


@functools.cache
def get_templates(
    user: Annotated[models.User, Depends(get_current_user)],
) -> Jinja2Templates:
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

    templates.env.globals['_'] = functools.partial(localization.gettext, user=user)
    return templates
