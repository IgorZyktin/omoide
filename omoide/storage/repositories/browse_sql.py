# -*- coding: utf-8 -*-
"""SQL queries for browse.
"""
GET_NESTED_ITEMS = """
WITH RECURSIVE nested_items AS (
    SELECT parent_uuid,
           owner_uuid,
           uuid,
           number,
           is_collection,
           name,
           thumbnail_ext
    FROM items
    WHERE uuid = :item_uuid
    UNION ALL
    SELECT i.parent_uuid,
           i.owner_uuid,
           i.uuid,
           i.number,
           i.is_collection,
           i.name,
           i.thumbnail_ext
    FROM items i
             inner join nested_items it2 on i.parent_uuid = it2.uuid
)
SELECT owner_uuid,
       uuid,
       is_collection,
       name,
       thumbnail_ext
FROM nested_items
WHERE uuid <> :item_uuid
ORDER BY number
LIMIT :limit OFFSET :offset;
"""

COUNT_NESTED_ITEMS = """
WITH RECURSIVE nested_items AS (
    SELECT parent_uuid,
           uuid
    FROM items
    WHERE uuid = :item_uuid
    UNION ALL
    SELECT i.parent_uuid,
           i.uuid
    FROM items i
             inner join nested_items it2 on i.parent_uuid = it2.uuid
)
SELECT count(*) AS total_items
FROM nested_items;
"""
