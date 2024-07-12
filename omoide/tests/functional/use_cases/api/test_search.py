"""Tests."""
import pytest
import pytest_asyncio

from omoide.storage.implementations.asyncpg.repositories.rp_search import SearchRepository


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


@pytest.fixture(scope='session')
def search_repo_input_1():
    """Return testing data."""
    return {
        'aa': 1,
        'ab': 2,
        'ac': 3,
        'ad': 4,
        'ae': 5,
    }


@pytest.fixture(scope='session')
def search_repo_input_2():
    """Return testing data."""
    return {
        'az': 40,
    }


@pytest.fixture(scope='session')
def search_repo_output_1():
    """Return testing data."""
    return [
        # core_models.GuessResult(tag='ae', counter=5),
        # core_models.GuessResult(tag='ad', counter=4),
        # core_models.GuessResult(tag='ac', counter=3),
        # core_models.GuessResult(tag='ab', counter=2),
        # core_models.GuessResult(tag='aa', counter=1),
    ]


@pytest.fixture(scope='session')
def search_repo_output_2():
    """Return testing data."""
    return [
        # core_models.GuessResult(tag='az', counter=40),
        # core_models.GuessResult(tag='ae', counter=5),
        # core_models.GuessResult(tag='ad', counter=4),
        # core_models.GuessResult(tag='ac', counter=3),
        # core_models.GuessResult(tag='ab', counter=2),
        # core_models.GuessResult(tag='aa', counter=1),
    ]


@pytest.mark.usefixtures('ensure_there_is_no_known_tags')
async def test_autocomplete_anon(
        functional_tests_anon_user,
        functional_tests_search_repo,
        functional_tests_testing_repo,
        search_repo_input_1,
        search_repo_input_2,
        search_repo_output_1,
        search_repo_output_2,
):
    """Test whole autocomplete life cycle for anon user."""
    # arrange
    # user = functional_tests_anon_user
    # search_repo = functional_tests_search_repo
    # testing_repo = functional_tests_testing_repo
    # limit = 10
    #
    # search_uc = uc_api_search.ApiSuggestTagUseCase(search_repo)
    #
    # # ensure emptiness --------------------------------------------------------
    # assert await search_uc.execute(user, '', limit) == []
    #
    # # populate database -------------------------------------------------------
    # await testing_repo.insert_known_tags_for_anon_user(search_repo_input_1)
    #
    # # check guesses -----------------------------------------------------------
    # result_1 = await search_uc.execute(user, 'a', limit)
    # assert result_1 == search_repo_output_1
    #
    # # populate database again -------------------------------------------------
    # await testing_repo.insert_known_tags_for_anon_user(search_repo_input_2)
    #
    # # check guesses -----------------------------------------------------------
    # result_2 = await search_uc.execute(user, 'a', limit)
    # assert result_2 == search_repo_output_2


@pytest.mark.usefixtures('ensure_there_is_no_known_tags')
async def test_autocomplete_anon_limit(
        functional_tests_anon_user,
        functional_tests_search_repo,
        functional_tests_testing_repo,
        search_repo_input_1,
):
    """Test whole autocomplete life cycle for anon user."""
    # arrange
    # user = functional_tests_anon_user
    # search_repo = functional_tests_search_repo
    # testing_repo = functional_tests_testing_repo
    # limit = 3
    #
    # search_uc = uc_api_search.ApiSuggestTagUseCase(search_repo)
    #
    # # populate database -------------------------------------------------------
    # await testing_repo.insert_known_tags_for_anon_user(search_repo_input_1)
    #
    # # check guesses -----------------------------------------------------------
    # result = await search_uc.execute(user, 'a', limit)
    # assert len(result) == limit


@pytest.mark.usefixtures('ensure_there_is_no_known_tags')
async def test_autocomplete_known(
        functional_tests_permanent_user,
        functional_tests_search_repo,
        functional_tests_testing_repo,
        search_repo_input_1,
        search_repo_input_2,
        search_repo_output_1,
        search_repo_output_2,
):
    """Test whole autocomplete life cycle for known user."""
    # arrange
    # user = functional_tests_permanent_user
    # search_repo = functional_tests_search_repo
    # testing_repo = functional_tests_testing_repo
    # limit = 10
    #
    # search_uc = uc_api_search.ApiSuggestTagUseCase(search_repo)
    #
    # # ensure emptiness --------------------------------------------------------
    # assert await search_uc.execute(user, '', limit) == []
    #
    # # populate database -------------------------------------------------------
    # await testing_repo.insert_known_tags_for_known_user(
    #     user.uuid,
    #     search_repo_input_1,
    # )
    #
    # # check guesses -----------------------------------------------------------
    # result_1 = await search_uc.execute(user, 'a', limit)
    # assert result_1 == search_repo_output_1
    #
    # # populate database again -------------------------------------------------
    # await testing_repo.insert_known_tags_for_known_user(
    #     user.uuid,
    #     search_repo_input_2,
    # )
    #
    # # check guesses -----------------------------------------------------------
    # result_2 = await search_uc.execute(user, 'a', limit)
    # assert result_2 == search_repo_output_2


@pytest.mark.usefixtures('ensure_there_is_no_known_tags')
async def test_autocomplete_not_mixing(
        functional_tests_permanent_user,
        functional_tests_anon_user,
        functional_tests_search_repo,
        functional_tests_testing_repo,
):
    """Test that different users get different tags."""
    # arrange
    # known_user = functional_tests_permanent_user
    # anon_user = functional_tests_anon_user
    # search_repo = functional_tests_search_repo
    # testing_repo = functional_tests_testing_repo
    # limit = 10
    #
    # search_uc = uc_api_search.ApiSuggestTagUseCase(search_repo)
    #
    # expected_anon_1 = [core_models.GuessResult(tag='affordable', counter=799)]
    # expected_anon_2 = []
    # expected_known_1 = [core_models.GuessResult(tag='private', counter=5)]
    # expected_known_2 = []
    #
    # # ensure emptiness --------------------------------------------------------
    # assert await search_uc.execute(known_user, '', limit) == []
    # assert await search_uc.execute(anon_user, '', limit) == []
    #
    # # populate database -------------------------------------------------------
    # await testing_repo.insert_known_tags_for_known_user(
    #     known_user.uuid,
    #     {
    #         'private': 5,
    #         'luxury': 8,
    #     }
    # )
    #
    # await testing_repo.insert_known_tags_for_anon_user(
    #     {
    #         'cheap': 55,
    #         'affordable': 799,
    #     }
    # )
    #
    # # check guesses -----------------------------------------------------------
    # anon_1 = await search_uc.execute(anon_user, 'af', limit)
    # anon_2 = await search_uc.execute(anon_user, 'pr', limit)
    #
    # known_1 = await search_uc.execute(known_user, 'pr', limit)
    # known_2 = await search_uc.execute(known_user, 'af', limit)
    #
    # assert anon_1 == expected_anon_1
    # assert anon_2 == expected_anon_2
    #
    # assert known_1 == expected_known_1
    # assert known_2 == expected_known_2
