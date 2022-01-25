# -*- coding: utf-8 -*-
"""SQL queries.
"""
USER_IS_PUBLIC = """
SELECT 1 
FROM public_users
WHERE user_uuid = :user_uuid;
"""

COUNT_ITEMS_OF_PUBLIC_USER = """
SELECT count(*) AS total_items
FROM items
WHERE owner_uuid = :owner_uuid
  AND parent_uuid IS NULL;
"""

GET_ITEMS_OF_PUBLIC_USER = """
SELECT owner_uuid,
       uuid,
       number,
       is_collection,
       name,
       thumbnail_ext
FROM items
WHERE owner_uuid = :owner_uuid
  AND parent_uuid IS NULL
ORDER BY number LIMIT :limit OFFSET :offset
"""

# FIXME
COUNT_ITEMS_OF_PRIVATE_USER = """
"""

# FIXME
GET_ITEMS_OF_PRIVATE_USER = """
"""
