"""Perform full recalculation of known tags."""

from omoide.database.implementations import impl_sqlalchemy
from omoide.omoide_cli import utils


async def run():
    """Entry point."""
    db_url = utils.get_env('OMOIDE__DB_URL_ADMIN')
    database = impl_sqlalchemy.SqlalchemyDatabase(
        db_url=db_url,
        echo=False,
    )
    users_repo = impl_sqlalchemy.UsersRepo()
    tags_repo = impl_sqlalchemy.TagsRepo()

    try:
        async with database.transaction() as conn:
            users = await users_repo.select(conn)
            for user in users:
                existing_known_tags = await tags_repo.get_known_tags_user(conn, user)
                actual_known_tags = await tags_repo.calculate_known_tags_user(
                    conn, user, only_tags=None
                )
                if existing_known_tags != actual_known_tags:
                    print(f'Saving {user.name}')  # noqa: T201
                    await tags_repo.insert_known_tags_user(
                        conn, user, actual_known_tags, batch_size=1000
                    )

            existing_known_tags_anon = await tags_repo.get_known_tags_anon(conn)
            actual_known_tags_anon = await tags_repo.calculate_known_tags_anon(conn, only_tags=None)
            if existing_known_tags_anon != actual_known_tags_anon:
                print('Saving anon')  # noqa: T201
                await tags_repo.insert_known_tags_anon(
                    conn, actual_known_tags_anon, batch_size=1000
                )
    finally:
        await database.disconnect()
