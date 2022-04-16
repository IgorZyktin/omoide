# -*- coding: utf-8 -*-
"""Authentication variants.
"""
import bcrypt

from omoide.domain import interfaces

__all__ = [
    'BcryptAuthenticator',
]


class BcryptAuthenticator(interfaces.AbsAuthenticator):
    """Authenticator that uses bcrypt algorithm."""

    def __init__(self, complexity: int) -> None:
        """Initialize instance."""
        self.complexity = complexity

    def encode_password(self, given_password: bytes | str) -> bytes:
        """Encode user password with chosen algorithm."""
        if isinstance(given_password, str):
            given_password = given_password.encode('utf-8')
        return bcrypt.hashpw(given_password, bcrypt.gensalt(self.complexity))

    def password_is_correct(
            self,
            given_password: bytes,
            reference: bytes,
    ) -> bool:
        """Return True if user password is correct."""
        return bcrypt.checkpw(given_password, reference)
