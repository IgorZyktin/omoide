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
           thumbnail_ext as ext
    FROM items
    WHERE uuid = :item_uuid
    UNION ALL
    SELECT i.parent_uuid,
           i.owner_uuid,
           i.uuid,
           i.number,
           i.is_collection,
           i.name,
           i.thumbnail_ext as ext
    FROM items i
             inner join nested_items it2 on i.parent_uuid = it2.uuid
)
SELECT owner_uuid,
       uuid,
       is_collection,
       name,
       ext,
       (select count(*) from nested_items) as total_items
FROM nested_items
WHERE uuid <> :item_uuid
ORDER BY number
LIMIT :limit OFFSET :offset;
"""
