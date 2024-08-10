"""Tests."""

from omoide import infra


def test_authenticator():
    password = 'qwerty12345'
    authenticator = infra.BcryptAuthenticator(complexity=4)

    assert authenticator.password_is_correct(
        given_password=password,
        reference=authenticator.encode_password(password),
    )
