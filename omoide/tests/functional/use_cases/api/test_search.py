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
        functional_tests_permanent_user,
        functional_tests_testing_repo,
):
    """Delete all corresponding known tags before and after all tests."""
    user = functional_tests_permanent_user
    testing_repo = functional_tests_testing_repo

    await testing_repo.drop_known_tags_for_known_user(user.uuid)
    await testing_repo.drop_known_tags_for_anon_user()
    yield
    await testing_repo.drop_known_tags_for_known_user(user.uuid)
    await testing_repo.drop_known_tags_for_anon_user()


@pytest.mark.usefixtures('ensure_there_is_no_known_tags')
async def test_autocomplete(
        functional_tests_permanent_user,
        functional_tests_anon_user,
        functional_tests_search_repo,
        functional_tests_testing_repo,
):
    """Test whole autocomplete life cycle."""
    # arrange
    known_user = functional_tests_permanent_user
    anon_user = functional_tests_anon_user
    search_repo = functional_tests_search_repo
    testing_repo = functional_tests_testing_repo
    limit = 10

    search_uc = uc_api_search.ApiSuggestTagUseCase(search_repo)

    # ensure emptiness --------------------------------------------------------
    assert await search_uc.execute(known_user, '', limit) == []
    assert await search_uc.execute(anon_user, '', limit) == []

    # populate database -------------------------------------------------------
    await testing_repo.insert_known_tags_for_known_user(
        known_user.uuid, {'private': 5, 'luxury': 8})
    await testing_repo.insert_known_tags_for_anon_user(
        {'cheap': 55, 'affordable': 799})

    # check guesses -----------------------------------------------------------
    known_1 = await search_uc.execute(known_user, 'pr', limit)
    known_2 = await search_uc.execute(known_user, 'af', limit)
    anon_1 = await search_uc.execute(anon_user, 'af', limit)
    anon_2 = await search_uc.execute(anon_user, 'pr', limit)
    assert [x.tag for x in known_1] == ['private']
    assert [x.tag for x in anon_1] == ['affordable']
    assert sum(x.counter for x in known_1) == 5
    assert sum(x.counter for x in anon_1) == 799
    # making sure that search results are not mixing
    assert [x.tag for x in known_2] == []
    assert [x.tag for x in anon_2] == []

    # populate database again -------------------------------------------------
    await testing_repo.insert_known_tags_for_known_user(
        known_user.uuid,
        {'aaa': 1, 'aab': 2, 'aac': 3, 'aad': 4, 'aae': 5},
    )
    await testing_repo.insert_known_tags_for_anon_user(
        {'aaa': 1, 'aab': 2, 'aac': 3, 'aad': 4, 'aae': 5},
    )

    # check guesses -----------------------------------------------------------
    small_limit = 3
    known_3 = await search_uc.execute(known_user, 'aa', limit=small_limit)
    anon_3 = await search_uc.execute(anon_user, 'aa', limit=small_limit)
    assert [x.tag for x in known_3] == ['aae', 'aad', 'aac']
    assert [x.tag for x in anon_3] == ['aae', 'aad', 'aac']
    assert sum(x.counter for x in known_3) == 12
    assert sum(x.counter for x in anon_3) == 12
