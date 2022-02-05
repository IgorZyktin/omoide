# -*- coding: utf-8 -*-
"""SQL queries.
"""
COUNT_ITEMS_OF_PUBLIC_USER = """
SELECT count(*) AS total_items
FROM items
WHERE owner_uuid = :owner_uuid
  AND parent_uuid IS NULL;
"""
