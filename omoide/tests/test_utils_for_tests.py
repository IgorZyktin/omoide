"""Tests for test infrastructure.
"""
import pytest

from omoide.domain import errors
from omoide.tests import utils


class Error1(errors.Error):
    """Dummy error for tests."""


class Error2(errors.Error):
    """Dummy error for tests."""


class Error3(errors.Error):
    """Dummy error for tests."""


def test_assert_error_bad_input_type():
    """Must raise on incorrect type."""
    # arrange
    error = None

    # assert
    msg = 'Expected to get subclass of Error, got NoneType instead'
    with pytest.raises(TypeError, match=msg):
        utils.assert_error(error, errors.Error)


def test_assert_error_bad_error_type():
    """Must raise on incorrect type."""
    # arrange
    error = Error1()

    # assert
    msg = 'Expected to get type Error2, got type Error1'
    with pytest.raises(TypeError, match=msg):
        utils.assert_error(error, Error2)


def test_assert_error_bad_error_types():
    """Must raise on incorrect type."""
    # arrange
    error = Error1()

    # assert
    msg = (r"Expected to get one of types \('Error2', 'Error3'\), "
           r"got type Error1")
    with pytest.raises(TypeError, match=msg):
        utils.assert_error(
            error,
            (Error2, Error3),
        )


def test_assert_error_good_regex():
    """Must point out that regex could be incorrectly read."""
    # arrange
    error = errors.Error(template='test')

    # assert
    assert utils.assert_error(error, errors.Error, 'test') == error


def test_assert_error_bad_not_found_regex():
    """Must fail because of unmatched regex."""
    # arrange
    error = errors.Error(template='foo')

    # assert
    msg = 'Regex pattern did not match'
    with pytest.raises(ValueError, match=msg):
        utils.assert_error(error, errors.Error, 'test')
