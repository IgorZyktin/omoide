# -*- coding: utf-8 -*-
"""SQL queries for search.
"""
TOTAL_RANDOM_ANON = """
SELECT count(*) AS total_items
FROM items
WHERE owner_uuid IN (SELECT user_uuid FROM public_users);
"""

TOTAL_SPECIFIC_ANON = """
SELECT count(*) AS total_items
FROM items it
         RIGHT JOIN computed_tags ct ON ct.item_uuid = it.uuid
WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
  AND ct.tags @> :tags_include
  AND NOT ct.tags && :tags_exclude;
"""

SEARCH_RANDOM_ANON = """
SELECT uuid, 
       parent_uuid,
       owner_uuid,
       number,
       name,
       is_collection,
       content_ext,
       preview_ext,
       thumbnail_ext
FROM items
WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
ORDER BY random() LIMIT :limit OFFSET :offset
"""

SEARCH_SPECIFIC_ANON = """
SELECT uuid, 
       parent_uuid,
       owner_uuid,
       number,
       name,
       is_collection,
       content_ext,
       preview_ext,
       thumbnail_ext,
       ct.tags
FROM items it
         RIGHT JOIN computed_tags ct ON ct.item_uuid = it.uuid
WHERE owner_uuid IN (SELECT user_uuid FROM public_users)
  AND ct.tags @> :tags_include
  AND NOT ct.tags && :tags_exclude
ORDER BY number LIMIT :limit OFFSET :offset;
"""
