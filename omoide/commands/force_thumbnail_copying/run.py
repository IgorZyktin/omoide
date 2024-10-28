"""Collection to force copying of thumbnails."""

from uuid import UUID

from sqlalchemy.orm import Session

from omoide import const
from omoide import custom_logging
from omoide import utils
from omoide.commands import helpers
from omoide.commands.force_thumbnail_copying.cfg import Config
from omoide.database import db_models
from omoide.storage.database.sync_db import SyncDatabase

LOG = custom_logging.get_logger(__name__)


def run(config: Config, database: SyncDatabase) -> None:
    """Copy thumbnail from children to parents."""
    LOG.info('\nConfig:\n{}', utils.serialize_model(config))

    with database.start_session() as session:
        users = helpers.get_all_corresponding_users(session, config.only_users)

    total_operations = 0

    for user in users:
        LOG.info('Copying covers for user {} {}', user.uuid, user.name)

        with database.start_session() as session:
            already_handled: set[UUID] = set()
            leaf_items = get_leaf_items(session, user)

            changed = 0
            for item in leaf_items:
                changed += force_copy_to_all_parents(session, item, already_handled)
                total_operations += changed
            LOG.info('Changed {} items', changed)
            session.commit()

    LOG.info('Total operations: {}', total_operations)


def get_leaf_items(
    session: Session,
    user: db_models.User,
) -> list[db_models.Item]:
    """Get all items without children."""
    stmt = """
    SELECT *
    FROM items AS leaf
    LEFT OUTER JOIN items AS child on child.parent_uuid = leaf.uuid
    WHERE child.uuid IS NULL and leaf.owner_uuid = :user_uuid
    AND leaf.content_ext IS NOT NULL
    AND leaf.preview_ext IS NOT NULL
    AND leaf.thumbnail_ext IS NOT NULL
    ORDER BY leaf.number
    """

    values = {
        'user_uuid': str(user.uuid),
    }

    response = session.execute(stmt, values).fetchall()  # type: ignore

    return [
        db_models.Item(
            uuid=x[0],
            parent_uuid=x[1],
            owner_uuid=x[2],
            number=x[3],
            name=x[4],
            is_collection=x[5],
            content_ext=x[6],
            preview_ext=x[7],
            thumbnail_ext=x[8],
            tags=x[9],
            permissions=x[10],
        )
        for x in response
    ]


def force_copy_to_all_parents(
    session: Session,
    item: db_models.Item,
    already_handled: set[UUID],
) -> int:
    """Copy data from given item to all parents."""
    changed = 0
    leaf_metainfo = helpers.get_metainfo(session, item)
    parent_uuid = item.parent_uuid

    while parent_uuid is not None:
        parent = helpers.get_item(session, parent_uuid)
        parent_metainfo = helpers.get_metainfo(session, item)

        if parent.uuid not in already_handled:
            copy_properties(session, parent, parent_metainfo, item, leaf_metainfo)
            invoke_worker_to_copy(session, parent, item)
            already_handled.add(parent.uuid)
            changed += 1

        parent_uuid = parent.parent_uuid

    return changed


def copy_properties(
    session: Session,
    parent: db_models.Item,
    parent_metainfo: db_models.Metainfo,
    child: db_models.Item,
    child_metainfo: db_models.Metainfo,
) -> None:
    """Copy basic parameters."""
    parent.thumbnail_ext = child.thumbnail_ext

    parent_metainfo.thumbnail_width = child_metainfo.thumbnail_width
    parent_metainfo.thumbnail_height = child_metainfo.thumbnail_height
    parent_metainfo.thumbnail_size = child_metainfo.thumbnail_size

    helpers.insert_item_note(
        session=session,
        item=parent,
        key='copied_image_from',
        value=str(child.uuid),
    )

    parent_metainfo.updated_at = utils.now()


def invoke_worker_to_copy(
    session: Session,
    parent: db_models.Item,
    child: db_models.Item,
) -> None:
    """Write info in the db so worker could complete the job."""
    copy = db_models.CommandCopy(
        created_at=utils.now(),
        processed_at=None,
        error='',
        owner_uuid=parent.owner_uuid,
        source_uuid=child.uuid,
        target_uuid=parent.uuid,
        media_type=const.THUMBNAIL,
        ext=child.thumbnail_ext or '',
    )
    session.add(copy)
    session.flush([copy])
