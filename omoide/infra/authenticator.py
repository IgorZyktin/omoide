"""Authentication variants."""

import bcrypt

from omoide import interfaces


class BcryptAuthenticator(interfaces.AbsAuthenticator):
    """Authenticator that uses bcrypt algorithm."""

    def encode_password(
        self,
        given_password: str,
        auth_complexity: int,
    ) -> str:
        """Encode user password with chosen algorithm."""
        result = bcrypt.hashpw(
            password=given_password.encode('utf-8'),
            salt=bcrypt.gensalt(auth_complexity),
        )
        return result.decode('utf-8')

    def password_is_correct(
        self,
        given_password: str,
        reference: str,
        auth_complexity: int,
    ) -> bool:
        """Return True if user password is correct."""
        return bcrypt.checkpw(
            password=given_password.encode('utf-8'),
            hashed_password=reference.encode('utf-8'),
        )
