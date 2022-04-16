# -*- coding: utf-8 -*-
"""Interface for authentication policy.
"""

import abc


class AbsAuthenticator(abc.ABC):
    """Abstract authenticator."""

    @abc.abstractmethod
    def encode_password(self, given_password: bytes) -> bytes:
        """Encode user password with chosen algorithm."""

    @abc.abstractmethod
    def password_is_correct(
            self,
            given_password: bytes,
            reference: bytes,
    ) -> bool:
        """Return True if user password is correct."""
