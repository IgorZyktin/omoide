"""Database implementation of the domain.

PostgreSQL specific because application needs arrays.
"""
# TODO - move actual models here
from omoide.storage.database.models import EXIF
from omoide.storage.database.models import KnownTags
from omoide.storage.database.models import KnownTagsAnon

_ = EXIF
_ = KnownTags
_ = KnownTagsAnon
