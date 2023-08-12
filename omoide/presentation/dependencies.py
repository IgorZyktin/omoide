# -*- coding: utf-8 -*-
"""External components.
"""
import binascii
from base64 import b64decode
from typing import Annotated
from typing import Any
from typing import Optional

from databases import Database
from fastapi import Depends
from fastapi.security import HTTPBasicCredentials
from starlette.requests import Request

from omoide import infra
from omoide import use_cases
from omoide import utils
from omoide.domain import auth
from omoide.domain import interfaces
from omoide.domain.storage.interfaces.in_rp_exif import AbsEXIFRepository
from omoide.domain.storage.interfaces.in_rp_media import AbsMediaRepository
from omoide.domain.interfaces.infra.in_policy import AbsPolicy
from omoide.presentation import app_config
from omoide.presentation import constants
from omoide.presentation import web
from omoide.storage.repositories import asyncpg


@utils.memorize
def get_config() -> app_config.Config:
    """Get config instance."""
    return app_config.Config()


_URL_CACHE: dict[tuple[str, Any], str] = {}


@utils.memorize
def get_templates() -> web.TemplateEngine:
    """Get templates instance."""
    config = get_config()

    def _https_url_for(
            request: Request,
            name: str,
            **path_params: Any,
    ) -> str:
        """Rewrite static files to HTTPS if on prod and cache result."""
        key = (name, tuple(path_params.items()))
        url = _URL_CACHE.get(key)
        if url is None:
            raw_url = request.url_for(name, **path_params)
            url = str(raw_url).replace('http:', 'https:', 1)
            _URL_CACHE[key] = url
        return url

    def _url_for(
            request: Request,
            name: str,
            **path_params: Any,
    ) -> str:
        """Basic url_for."""
        key = (name, tuple(path_params.items()))
        url = _URL_CACHE.get(key)
        if url is None:
            url = str(request.url_for(name, **path_params))
            _URL_CACHE[key] = url
        return url

    if config.env != 'prod':
        templates = web.TemplateEngine(
            directory='omoide/presentation/templates',
            url_for=_url_for,
        )
        templates.env.globals['url_for'] = _url_for

    else:
        templates = web.TemplateEngine(
            directory='omoide/presentation/templates',
            url_for=_https_url_for,
        )
        templates.env.globals['url_for'] = _https_url_for

    templates.env.globals['zip'] = zip

    return templates


@utils.memorize
def get_db() -> Database:
    """Get database instance."""
    return Database(get_config().db_url_app.get_secret_value())


# repositories ----------------------------------------------------------------


@utils.memorize
def get_search_repo() -> interfaces.AbsSearchRepository:
    """Get repo instance."""
    return asyncpg.SearchRepository(get_db())


@utils.memorize
def get_preview_repo() -> interfaces.AbsPreviewRepository:
    """Get repo instance."""
    return asyncpg.PreviewRepository(get_db())


@utils.memorize
def get_browse_repo() -> interfaces.AbsBrowseRepository:
    """Get repo instance."""
    return asyncpg.BrowseRepository(get_db())


@utils.memorize
def get_users_read_repo() -> interfaces.AbsUsersReadRepository:
    """Get repo instance."""
    return asyncpg.UsersReadRepository(get_db())


@utils.memorize
def get_users_write_repo() -> interfaces.AbsUsersWriteRepository:
    """Get repo instance."""
    return asyncpg.UsersWriteRepository(get_db())


@utils.memorize
def get_items_read_repo() -> interfaces.AbsItemsReadRepository:
    """Get repo instance."""
    return asyncpg.ItemsReadRepository(get_db())


@utils.memorize
def get_items_write_repo() -> interfaces.AbsItemsWriteRepository:
    """Get repo instance."""
    return asyncpg.ItemsWriteRepository(get_db())


def media_repo() -> AbsMediaRepository:
    """Get repo instance."""
    return asyncpg.MediaRepository(get_db())


def exif_repo() -> AbsEXIFRepository:
    """Get repo instance."""
    return asyncpg.EXIFRepository(get_db())


@utils.memorize
def get_metainfo_repo() -> interfaces.AbsMetainfoRepository:
    """Get repo instance."""
    return asyncpg.MetainfoRepository(get_db())


# application specific objects ------------------------------------------------


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


@utils.memorize
def get_auth_use_case(
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
) -> use_cases.AuthUseCase:
    """Get use case instance."""
    return use_cases.AuthUseCase(
        users_repo=users_read_repository,
    )


@utils.memorize
def get_authenticator() -> interfaces.AbsAuthenticator:
    """Get authenticator instance."""
    return infra.BcryptAuthenticator(
        complexity=4,  # minimal
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


@utils.memorize
def get_policy(
        items_read_repository:
        interfaces.AbsItemsReadRepository = Depends(get_items_read_repo),
) -> interfaces.AbsPolicy:
    """Get policy instance."""
    return infra.Policy(
        items_repo=items_read_repository,
    )


# application related use cases -----------------------------------------------


@utils.memorize
def app_dynamic_search_use_case(
        search_repository:
        interfaces.AbsSearchRepository = Depends(get_search_repo),
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
) -> use_cases.AppDynamicSearchUseCase:
    """Get use case instance."""
    return use_cases.AppDynamicSearchUseCase(
        search_repo=search_repository,
        browse_repo=browse_repository,
    )


@utils.memorize
def app_paged_search_use_case(
        search_repository:
        interfaces.AbsSearchRepository = Depends(get_search_repo),
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
) -> use_cases.AppPagedSearchUseCase:
    """Get use case instance."""
    return use_cases.AppPagedSearchUseCase(
        search_repo=search_repository,
        browse_repo=browse_repository,
    )


@utils.memorize
def app_preview_use_case(
        preview_repository:
        interfaces.AbsPreviewRepository = Depends(get_preview_repo),
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
        items_read_repository:
        interfaces.AbsItemsReadRepository = Depends(get_items_read_repo),
        metainfo_repo:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.AppPreviewUseCase:
    """Get use case instance."""
    return use_cases.AppPreviewUseCase(
        preview_repo=preview_repository,
        users_repo=users_read_repository,
        items_repo=items_read_repository,
        meta_repo=metainfo_repo,
    )


@utils.memorize
def app_browse_use_case(
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
        items_read_repository:
        interfaces.AbsItemsReadRepository = Depends(get_items_read_repo),
        metainfo_repo:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.AppBrowseUseCase:
    """Get use case instance."""
    return use_cases.AppBrowseUseCase(
        browse_repo=browse_repository,
        users_repo=users_read_repository,
        items_repo=items_read_repository,
        meta_repo=metainfo_repo
    )


@utils.memorize
def app_home_use_case(
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
) -> use_cases.AppHomeUseCase:
    """Get use case instance."""
    return use_cases.AppHomeUseCase(
        browse_repo=browse_repository,
    )


@utils.memorize
def app_upload_use_case(
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
        items_read_repository:
        interfaces.AbsItemsReadRepository = Depends(get_items_read_repo),
) -> use_cases.AppUploadUseCase:
    """Get use case instance."""
    return use_cases.AppUploadUseCase(
        items_repo=items_read_repository,
        users_repo=users_read_repository,
    )


# app item related use cases --------------------------------------------------


@utils.memorize
def api_search_use_case(
        search_repository:
        interfaces.AbsSearchRepository = Depends(get_search_repo),
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
) -> use_cases.ApiSearchUseCase:
    """Get use case instance."""
    return use_cases.ApiSearchUseCase(
        search_repo=search_repository,
        browse_repo=browse_repository,
    )


def api_suggest_tag_use_case(
        search_repository:
        interfaces.AbsSearchRepository = Depends(get_search_repo),
) -> use_cases.ApiSuggestTagUseCase:
    """Get use case instance."""
    return use_cases.ApiSuggestTagUseCase(search_repo=search_repository)


@utils.memorize
def app_item_create_use_case(
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
) -> use_cases.AppItemCreateUseCase:
    """Get use case instance."""
    return use_cases.AppItemCreateUseCase(
        users_repo=users_read_repository,
        items_repo=items_write_repository,
    )


@utils.memorize
def app_item_update_use_case(
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.AppItemUpdateUseCase:
    """Get use case instance."""
    return use_cases.AppItemUpdateUseCase(
        users_repo=users_read_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def app_item_delete_use_case(
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
) -> use_cases.AppItemDeleteUseCase:
    """Get use case instance."""
    return use_cases.AppItemDeleteUseCase(
        items_repo=items_write_repository,
    )


@utils.memorize
def api_items_download_use_case(
        items_read_repository:
        interfaces.AbsItemsReadRepository = Depends(get_items_read_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemsDownloadUseCase:
    """Get use case instance."""
    return use_cases.ApiItemsDownloadUseCase(
        items_repo=items_read_repository,
        metainfo_repo=metainfo_repository,
    )


# api item related use cases --------------------------------------------------


@utils.memorize
def api_item_create_use_case(
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemCreateUseCase:
    """Get use case instance."""
    return use_cases.ApiItemCreateUseCase(
        users_repo=users_read_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def api_item_create_bulk_use_case(
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemCreateBulkUseCase:
    """Get use case instance."""
    return use_cases.ApiItemCreateBulkUseCase(
        users_repo=users_read_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def api_item_read_use_case(
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
) -> use_cases.ApiItemReadUseCase:
    """Get use case instance."""
    return use_cases.ApiItemReadUseCase(
        items_repo=items_write_repository,
    )


@utils.memorize
def api_item_update_use_case(
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemUpdateUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdateUseCase(
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def api_item_update_tags_use_case(
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemUpdateTagsUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdateTagsUseCase(
        users_repo=users_read_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def api_item_update_permissions_use_case(
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemUpdatePermissionsUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdatePermissionsUseCase(
        users_repo=users_read_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def api_item_copy_thumbnail_use_case(
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
        media_repository: AbsMediaRepository = Depends(media_repo),
) -> use_cases.ApiCopyThumbnailUseCase:
    """Get use case instance."""
    return use_cases.ApiCopyThumbnailUseCase(
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
        media_repo=media_repository,
    )


@utils.memorize
def api_item_update_parent_use_case(
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
        media_repository: AbsMediaRepository = Depends(media_repo),
) -> use_cases.ApiItemUpdateParentUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdateParentUseCase(
        users_repo=users_read_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
        media_repo=media_repository,
    )


@utils.memorize
def api_item_delete_use_case(
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemDeleteUseCase:
    """Get use case instance."""
    return use_cases.ApiItemDeleteUseCase(
        users_repo=users_read_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def api_browse_use_case(
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
) -> use_cases.APIBrowseUseCase:
    """Get use case instance."""
    return use_cases.APIBrowseUseCase(
        browse_repo=browse_repository,
    )


# api media related use cases -------------------------------------------------


def create_media_use_case(
        media_repository: AbsMediaRepository = Depends(media_repo),
) -> use_cases.CreateMediaUseCase:
    """Get use case instance."""
    return use_cases.CreateMediaUseCase(media_repo=media_repository)


# api exif related use cases -------------------------------------------------


def api_create_exif_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        exif_repository: Annotated[AbsEXIFRepository, Depends(exif_repo)],
) -> use_cases.CreateEXIFUseCase:
    """Get use case instance."""
    return use_cases.CreateEXIFUseCase(policy=policy,
                                       exif_repo=exif_repository)


def api_read_exif_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        exif_repository: Annotated[AbsEXIFRepository, Depends(exif_repo)],
) -> use_cases.ReadEXIFUseCase:
    """Get use case instance."""
    return use_cases.ReadEXIFUseCase(policy=policy,
                                     exif_repo=exif_repository)


def api_update_exif_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        exif_repository: Annotated[AbsEXIFRepository, Depends(exif_repo)],
) -> use_cases.UpdateEXIFUseCase:
    """Get use case instance."""
    return use_cases.UpdateEXIFUseCase(policy=policy,
                                       exif_repo=exif_repository)


def api_delete_exif_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        exif_repository: Annotated[AbsEXIFRepository, Depends(exif_repo)],
) -> use_cases.DeleteEXIFUseCase:
    """Get use case instance."""
    return use_cases.DeleteEXIFUseCase(policy=policy,
                                       exif_repo=exif_repository)


# api metainfo related use cases ----------------------------------------------


def read_metainfo_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        metainfo_repository: Annotated[interfaces.AbsMetainfoRepository,
                                       Depends(get_metainfo_repo)],
) -> use_cases.ReadMetainfoUseCase:
    """Get use case instance."""
    return use_cases.ReadMetainfoUseCase(policy=policy,
                                         meta_repo=metainfo_repository)


def update_metainfo_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        metainfo_repository: Annotated[interfaces.AbsMetainfoRepository,
                                       Depends(get_metainfo_repo)],
) -> use_cases.UpdateMetainfoUseCase:
    """Get use case instance."""
    return use_cases.UpdateMetainfoUseCase(policy=policy,
                                           meta_repo=metainfo_repository)


# app profile related use cases -----------------------------------------------


@utils.memorize
def profile_quotas_use_case(
        users_read_repository:
        interfaces.AbsUsersReadRepository = Depends(get_users_read_repo),
        items_read_repository:
        interfaces.AbsItemsReadRepository = Depends(get_items_read_repo),
) -> use_cases.AppProfileQuotasUseCase:
    """Get use case instance."""
    return use_cases.AppProfileQuotasUseCase(
        users_repo=users_read_repository,
        items_repo=items_read_repository,
    )


@utils.memorize
def profile_new_use_case(
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
) -> use_cases.APIProfileNewUseCase:
    """Get use case instance."""
    return use_cases.APIProfileNewUseCase(
        browse_repo=browse_repository,
    )


@utils.memorize
def profile_tags_use_case(
        search_repository:
        interfaces.AbsSearchRepository = Depends(get_search_repo),
) -> use_cases.AppProfileTagsUseCase:
    """Get use case instance."""
    return use_cases.AppProfileTagsUseCase(
        search_repo=search_repository,
    )
