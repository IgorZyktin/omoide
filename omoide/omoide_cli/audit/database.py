"""Audit database wrapper."""

from omoide.database.implementations.impl_sqlalchemy import SqlalchemyDatabase


class AuditDatabase(SqlalchemyDatabase):
    """Audit database wrapper."""
