# -*- coding: utf-8 -*-
"""SQL queries for preview.
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

GET_EXTENDED_ITEM = """
SELECT * 
FROM items
WHERE uuid = :item_uuid;
"""
