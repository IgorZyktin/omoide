"""Tests.
"""
import pytest
import pytest_asyncio

from omoide.storage.repositories.asyncpg.rp_search import SearchRepository
from omoide.use_cases.api import uc_api_search


@pytest.fixture(scope='session')
def functional_tests_search_repo(functional_tests_database):
    """Return repository for functional tests."""
    return SearchRepository(functional_tests_database)


@pytest_asyncio.fixture
async def ensure_there_is_no_known_tags(
        functional_tests_permanent_item,
        functional_tests_exif_repo,
):
    """Delete all corresponding known tags before and after all tests."""
    item = functional_tests_permanent_item
    exif_repo = functional_tests_exif_repo

    await exif_repo.delete_exif(item.uuid)
    yield
    await exif_repo.delete_exif(item.uuid)


@pytest.mark.usefixtures('ensure_there_is_no_known_tags')
async def test_autocomplete(
        functional_tests_permanent_user,
        functional_tests_anon_user,
        functional_tests_search_repo,
):
    """Test whole autocomplete life cycle."""
    # arrange
    known_user = functional_tests_permanent_user
    anon_user = functional_tests_anon_user
    search_repo = functional_tests_search_repo
    limit = 10

    search_uc = uc_api_search.ApiSuggestTagUseCase(search_repo)

    # ensure emptiness --------------------------------------------------------
    assert await search_uc.execute(known_user, 'text', limit) == []
    assert await search_uc.execute(anon_user, 'text', limit) == []

    # populate database -------------------------------------------------------
    # TODO

    # check guesses -----------------------------------------------------------
    # TODO

    # populate database again -------------------------------------------------
    # TODO

    # check guesses -----------------------------------------------------------
    # TODO

    # clear database ----------------------------------------------------------
    # TODO

    # ensure emptiness --------------------------------------------------------
    assert await search_uc.execute(known_user, 'text', limit) == []
    assert await search_uc.execute(anon_user, 'text', limit) == []
