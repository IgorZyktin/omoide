# -*- coding: utf-8 -*-
"""Database implementation of the domain.

PostgreSQL specific because application needs arrays.
"""
# TODO - remove after refactoring
from omoide.storage.database import db_models

ComputedTags = db_models.ComputedTags
Signature = db_models.Signature
OrphanFiles = db_models.OrphanFiles
KnownTags = db_models.KnownTags
KnownTagsAnon = db_models.KnownTagsAnon
LongJob = db_models.LongJob
Item = db_models.Item
Metainfo = db_models.Metainfo
Media = db_models.Media
CommandCopy = db_models.CommandCopy
