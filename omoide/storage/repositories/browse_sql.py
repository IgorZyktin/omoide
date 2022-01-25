# -*- coding: utf-8 -*-
"""SQL queries for browse.
"""
COUNT_ITEMS = """
SELECT count(*) AS total_items
FROM items
WHERE parent_uuid = :item_uuid;
"""

GET_ITEMS = """
SELECT owner_uuid,
       uuid,
       number,
       is_collection,
       name,
       thumbnail_ext
FROM items
WHERE parent_uuid = :item_uuid
AND uuid <> :item_uuid   
ORDER BY number
LIMIT :limit OFFSET :offset;
"""
