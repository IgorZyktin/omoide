# -*- coding: utf-8 -*-
"""SQL queries for search.
"""
COUNT_ITEMS_FOR_ANON_USER = """
SELECT count(*) AS total_items
FROM items it
         RIGHT JOIN computed_tags ct ON ct.item_uuid = it.uuid
WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
  AND ct.tags && :tags_include
  AND NOT ct.tags && :tags_exclude;
"""

SEARCH_RANDOM_ITEMS_FOR_ANON_USER = """
SELECT owner_uuid,
       uuid,
       number,
       is_collection,
       name,
       thumbnail_ext as ext
FROM items
WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
ORDER BY random() LIMIT :limit OFFSET :offset
"""

SEARCH_SPECIFIC_ITEMS_FOR_ANON_USER = """
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
  AND ct.tags && :tags_include
  AND NOT ct.tags && :tags_exclude
ORDER BY number LIMIT :limit OFFSET :offset;
"""
