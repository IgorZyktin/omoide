# -*- coding: utf-8 -*-
"""SQL queries.
"""

SEARCH_RANDOM_ITEMS_FOR_ANON_USER = """
WITH query AS (
    SELECT owner_uuid,
           uuid,
           number,
           is_collection,
           name,
           thumbnail_ext as ext
    FROM items
    WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
)
SELECT *
FROM (TABLE query ORDER BY random() LIMIT :limit OFFSET :offset) sub
         RIGHT JOIN (SELECT count(*) FROM query) c(full_count) ON true;
"""

SEARCH_SPECIFIC_ITEMS_FOR_ANON_USER = """
WITH query AS (
    SELECT owner_uuid,
           uuid,
           number,
           is_collection,
           name,
           thumbnail_ext as ext,
           ct.tags
    FROM items it
             RIGHT JOIN computed_tags ct ON ct.item_uuid = it.uuid
    WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
      AND ct.tags @> :tags_in
)
SELECT sub.owner_uuid,
       sub.uuid,
       sub.is_collection,
       sub.name,
       sub.ext,
       full_count
FROM (TABLE query ORDER BY query.number LIMIT :limit OFFSET :offset) sub
         RIGHT JOIN (SELECT count(*) FROM query) c(full_count) ON true;
"""
