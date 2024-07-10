"""Authentication variants."""
import bcrypt

from omoide.domain import interfaces


class BcryptAuthenticator(interfaces.AbsAuthenticator):
    """Authenticator that uses bcrypt algorithm."""

    def __init__(self, complexity: int) -> None:
        """Initialize instance."""
        self.complexity = complexity

    def encode_password(self, given_password: str) -> str:
        """Encode user password with chosen algorithm."""
        result = bcrypt.hashpw(
            password=given_password.encode('utf-8'),
            salt=bcrypt.gensalt(self.complexity),
        )
        return result.decode('utf-8')

    def password_is_correct(
        self,
        given_password: str,
        reference: str,
    ) -> bool:
        """Return True if user password is correct."""
        return bcrypt.checkpw(
            password=given_password.encode('utf-8'),
            hashed_password=reference.encode('utf-8'),
        )
