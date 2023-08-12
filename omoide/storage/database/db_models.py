"""Database implementation of the domain.

PostgreSQL specific because application needs arrays.
"""
# TODO - move actual models here
from omoide.storage.database import models

EXIF = models.EXIF
KnownTags = models.KnownTags
KnownTagsAnon = models.KnownTagsAnon
Media = models.Media
ManualCopy = models.ManualCopy
