CREATE OR REPLACE FUNCTION compute_tags(given_uuid UUID,
                                        OUT computed_tags text[])
AS
$$
BEGIN
    WITH RECURSIVE nested_items AS (
        SELECT parent_uuid,
               uuid,
               name,
               tags
        FROM items
        WHERE uuid = given_uuid
        UNION ALL
        SELECT i.parent_uuid,
               i.uuid,
               i.name,
               i.tags
        FROM items i
                 INNER JOIN nested_items it2 ON i.uuid = it2.parent_uuid
        WHERE i.name <> ''
    )
    SELECT INTO computed_tags array_agg(DISTINCT tags) as tags
    FROM (SELECT uuid,
                 unnest(array_cat (tags, ARRAY [lower(name), uuid::text])) as tags
          FROM nested_items) uniq;
END
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION insert_computed_tags() RETURNS TRIGGER AS
$$
BEGIN
    INSERT INTO computed_tags
    SELECT NEW.uuid, compute_tags(NEW.uuid)
    ON CONFLICT (item_uuid) DO UPDATE SET tags = excluded.tags;
    RETURN NULL;
END
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER item_altering
    AFTER INSERT OR UPDATE
    ON items
    FOR EACH ROW
EXECUTE FUNCTION insert_computed_tags();
