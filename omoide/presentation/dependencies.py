"""Dependencies."""

from base64 import b64decode
import binascii
from typing import Annotated

from databases import Database
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from omoide import const
from omoide import infra
from omoide import interfaces
from omoide import models
from omoide import use_cases
from omoide import utils
from omoide.infra.mediator import Mediator
from omoide.object_storage import interfaces as object_interfaces
from omoide.object_storage.implementations.file_server import FileObjectStorage
from omoide.omoide_app.auth.auth_use_cases import LoginUserUseCase
from omoide.presentation import app_config
from omoide.presentation import constants as app_constants
from omoide.presentation import web
from omoide.storage import interfaces as storage_interfaces
from omoide.storage.implementations import asyncpg


@utils.memorize
def get_config() -> app_config.Config:
    """Get config instance."""
    return app_config.Config()


@utils.memorize
def get_templates() -> Jinja2Templates:
    """Get templates instance."""
    templates = Jinja2Templates(directory='omoide/presentation/templates')
    templates.env.globals['zip'] = zip
    templates.env.globals['version'] = str(const.FRONTEND_VERSION)
    templates.env.globals['get_content_href'] = web.get_content_href
    templates.env.globals['get_preview_href'] = web.get_preview_href
    templates.env.globals['get_thumbnail_href'] = web.get_thumbnail_href
    templates.env.globals['human_readable_size'] = utils.human_readable_size
    templates.env.globals['sep_digits'] = utils.sep_digits
    return templates


@utils.memorize
def get_db() -> Database:
    """Get database instance."""
    return Database(get_config().db_url_app.get_secret_value())


@utils.memorize
def get_storage() -> storage_interfaces.AbsStorage:
    """Get storage instance."""
    return asyncpg.AsyncpgStorage(get_db())


# repositories ----------------------------------------------------------------


# TODO - remove
@utils.memorize
def get_search_repo() -> storage_interfaces.AbsSearchRepository:
    """Get repo instance."""
    return asyncpg.SearchRepository(get_db())


# TODO - remove
@utils.memorize
def get_signatures_repo() -> storage_interfaces.AbsSignaturesRepo:
    """Get repo instance."""
    return asyncpg.SignaturesRepo(get_db())


# TODO - remove
@utils.memorize
def get_browse_repo() -> storage_interfaces.AbsBrowseRepository:
    """Get repo instance."""
    return asyncpg.BrowseRepository(get_db())


# TODO - remove
@utils.memorize
def get_users_repo() -> storage_interfaces.AbsUsersRepo:
    """Get repo instance."""
    return asyncpg.UsersRepo(get_db())


# TODO - remove
@utils.memorize
def get_items_repo() -> storage_interfaces.AbsItemsRepo:
    """Get repo instance."""
    return asyncpg.ItemsRepo(get_db())


# TODO - remove
@utils.memorize
def get_media_repo() -> storage_interfaces.AbsMediaRepo:
    """Get repo instance."""
    return asyncpg.MediaRepo(get_db())


# TODO - remove
@utils.memorize
def get_exif_repo() -> storage_interfaces.AbsEXIFRepository:
    """Get repo instance."""
    return asyncpg.EXIFRepository(get_db())


# TODO - remove
@utils.memorize
def get_misc_repo() -> storage_interfaces.AbsMiscRepo:
    """Get repo instance."""
    return asyncpg.MiscRepo(get_db())


# TODO - remove
@utils.memorize
def get_metainfo_repo() -> storage_interfaces.AbsMetainfoRepo:
    """Get repo instance."""
    return asyncpg.MetainfoRepo(get_db())


# application specific objects ------------------------------------------------


def get_aim(request: Request) -> web.AimWrapper:
    """General way of getting aim."""
    params = dict(request.query_params)
    return web.AimWrapper.from_params(
        params=params,
        items_per_page=min(app_constants.ITEMS_PER_PAGE,
                           app_constants.MAX_ITEMS_PER_PAGE),
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


@utils.memorize
def get_authenticator() -> interfaces.AbsAuthenticator:
    """Get authenticator instance."""
    return infra.BcryptAuthenticator(complexity=const.AUTH_COMPLEXITY)


@utils.memorize
def get_policy(
    items_repo: storage_interfaces.AbsItemsRepo = Depends(get_items_repo),
) -> interfaces.AbsPolicy:
    """Get policy instance."""
    return infra.Policy(items_repo=items_repo)


@utils.memorize
def get_object_storage(
    media_repo: Annotated[storage_interfaces.AbsMediaRepo,
                          Depends(get_media_repo)],
) -> object_interfaces.AbsObjectStorage:
    """Get policy instance."""
    config = get_config()
    return FileObjectStorage(
        media_repo=media_repo,
        prefix_size=config.prefix_size,
    )


@utils.memorize
def get_mediator(
    authenticator: Annotated[interfaces.AbsAuthenticator,
                             Depends(get_authenticator)],
    browse_repo: Annotated[storage_interfaces.AbsBrowseRepository,
                           Depends(get_browse_repo)],
    exif_repo: Annotated[storage_interfaces.AbsEXIFRepository,
                         Depends(get_exif_repo)],
    items_repo: Annotated[storage_interfaces.AbsItemsRepo,
                          Depends(get_items_repo)],
    meta_repo: Annotated[storage_interfaces.AbsMetainfoRepo,
                         Depends(get_metainfo_repo)],
    misc_repo: Annotated[storage_interfaces.AbsMiscRepo,
                         Depends(get_misc_repo)],
    search_repo: Annotated[storage_interfaces.AbsSearchRepository,
                           Depends(get_search_repo)],
    signatures_repo: Annotated[storage_interfaces.AbsSignaturesRepo,
                               Depends(get_signatures_repo)],
    storage: Annotated[storage_interfaces.AbsStorage,
                       Depends(get_storage)],
    users_repo: Annotated[storage_interfaces.AbsUsersRepo,
                          Depends(get_users_repo)],
    object_storage: Annotated[object_interfaces.AbsObjectStorage,
                              Depends(get_object_storage)],
) -> Mediator:
    """Get mediator instance."""
    return Mediator(
        authenticator=authenticator,
        browse_repo=browse_repo,  # FIXME - app-related dependency
        exif_repo=exif_repo,
        items_repo=items_repo,
        meta_repo=meta_repo,
        misc_repo=misc_repo,
        search_repo=search_repo,
        storage=storage,
        signatures_repo=signatures_repo,
        users_repo=users_repo,
        object_storage=object_storage,
    )


async def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(get_credentials)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
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
        detail='You are not allowed to perform this operation',
    )


async def get_admin_user(
    current_user: Annotated[models.User, Depends(get_known_user)],
) -> models.User:
    """Return current user, raise if user is not admin."""
    if current_user.is_admin:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail='You are not allowed to perform this operation',
    )


# app item related use cases --------------------------------------------------


@utils.memorize
def app_item_update_use_case(
    users_repo: storage_interfaces.AbsUsersRepo = Depends(get_users_repo),
    items_repo: storage_interfaces.AbsItemsRepo = Depends(get_items_repo),
    meta_repo: storage_interfaces.AbsMetainfoRepo = Depends(get_metainfo_repo),
) -> use_cases.AppItemUpdateUseCase:
    """Get use case instance."""
    return use_cases.AppItemUpdateUseCase(
        users_repo=users_repo,
        items_repo=items_repo,
        metainfo_repo=meta_repo,
    )


@utils.memorize
def app_item_delete_use_case(
    items_repo: storage_interfaces.AbsItemsRepo = Depends(get_items_repo),
) -> use_cases.AppItemDeleteUseCase:
    """Get use case instance."""
    return use_cases.AppItemDeleteUseCase(
        items_repo=items_repo,
    )


# api item related use cases --------------------------------------------------


@utils.memorize
def api_item_update_use_case(
    items_repo: storage_interfaces.AbsItemsRepo = Depends(get_items_repo),
    meta_repo: storage_interfaces.AbsMetainfoRepo = Depends(get_metainfo_repo),
) -> use_cases.ApiItemUpdateUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdateUseCase(
        items_repo=items_repo,
        metainfo_repo=meta_repo,
    )


@utils.memorize
def api_item_update_tags_use_case(
    users_repo: Annotated[storage_interfaces.AbsUsersRepo,
                          Depends(get_users_repo)],
    items_repo: Annotated[storage_interfaces.AbsItemsRepo,
                          Depends(get_items_repo)],
    meta_repo: Annotated[storage_interfaces.AbsMetainfoRepo,
                         Depends(get_metainfo_repo)],
    misc_repo: Annotated[storage_interfaces.AbsMiscRepo,
                         Depends(get_misc_repo)],
) -> use_cases.ApiItemUpdateTagsUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdateTagsUseCase(
        users_repo=users_repo,
        items_repo=items_repo,
        metainfo_repo=meta_repo,
        misc_repo=misc_repo,
    )


@utils.memorize
def api_item_update_permissions_use_case(
    users_repo: Annotated[storage_interfaces.AbsUsersRepo,
                          Depends(get_users_repo)],
    items_repo: Annotated[storage_interfaces.AbsItemsRepo,
                          Depends(get_items_repo)],
    meta_repo: Annotated[storage_interfaces.AbsMetainfoRepo,
                         Depends(get_metainfo_repo)],
    misc_repo: Annotated[storage_interfaces.AbsMiscRepo,
                         Depends(get_misc_repo)],
) -> use_cases.ApiItemUpdatePermissionsUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdatePermissionsUseCase(
        users_repo=users_repo,
        items_repo=items_repo,
        metainfo_repo=meta_repo,
        misc_repo=misc_repo,
    )


@utils.memorize
def api_item_update_parent_use_case(
    policy: Annotated[interfaces.AbsPolicy, Depends(get_policy)],
    users_repo: Annotated[storage_interfaces.AbsUsersRepo,
                          Depends(get_users_repo)],
    items_repo: Annotated[storage_interfaces.AbsItemsRepo,
                          Depends(get_items_repo)],
    metainfo_repo: Annotated[storage_interfaces.AbsMetainfoRepo,
                             Depends(get_metainfo_repo)],
    media_repository: Annotated[storage_interfaces.AbsMediaRepo,
                                Depends(get_media_repo)],
    misc_repo: Annotated[
        storage_interfaces.AbsMiscRepo, Depends(get_misc_repo)],
) -> use_cases.ApiItemUpdateParentUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdateParentUseCase(
        policy=policy,
        users_repo=users_repo,
        items_repo=items_repo,
        metainfo_repo=metainfo_repo,
        media_repo=media_repository,
        misc_repo=misc_repo,
    )
