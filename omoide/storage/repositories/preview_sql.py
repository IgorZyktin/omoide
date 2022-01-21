# -*- coding: utf-8 -*-
"""SQL queries for preview.
"""
GET_ITEM = """
SELECT * 
FROM items
WHERE uuid = :item_uuid;
"""

GET_NEIGHBOURS = """
SELECT uuid
FROM items
WHERE parent_uuid = (SELECT parent_uuid FROM items WHERE uuid = :item_uuid);
"""
