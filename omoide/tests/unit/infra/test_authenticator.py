"""Tests."""

from omoide import infra


def test_authenticator():
    # arrange
    password = 'qwerty12345'
    authenticator = infra.BcryptAuthenticator()
    auth_complexity = 4

    # act + assert
    assert authenticator.password_is_correct(
        given_password=password,
        reference=authenticator.encode_password(password, auth_complexity),
        auth_complexity=auth_complexity,
    )
