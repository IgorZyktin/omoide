# -*- coding: utf-8 -*-
"""SQL queries.
"""
CHECK_ACCESS = """
SELECT owner_uuid,
       exists(SELECT 1
              FROM public_users pu
              WHERE pu.user_uuid = i.owner_uuid)  AS is_public,
       (SELECT :user_uuid = ANY (cp.permissions)) AS is_given
FROM items i
         LEFT JOIN computed_permissions cp ON cp.item_uuid = i.uuid
WHERE uuid = :item_uuid;
"""

GET_ANCESTORS = """
WITH RECURSIVE nested_items AS (
    SELECT parent_uuid,
           owner_uuid,
           uuid,
           is_collection,
           name,
           thumbnail_ext as ext
    FROM items
    WHERE uuid = :item_uuid
    UNION ALL
    SELECT i.parent_uuid,
           i.owner_uuid,
           i.uuid,
           i.is_collection,
           i.name,
           i.thumbnail_ext as ext
    FROM items i
             INNER JOIN nested_items it2 ON i.uuid = it2.parent_uuid
)
SELECT owner_uuid,
       uuid,
       is_collection,
       name,
       ext
FROM nested_items;
"""

GET_OWNER = """
SELECT uuid,
       name
FROM users
WHERE uuid = :user_uuid;
"""
