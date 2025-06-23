"""
Seed mongoDB with MySQL Data.
"""

from collections.abc import Sequence
from itertools import chain
import mongo_db  # noqa: F401
from mongoengine import QuerySet
from mongo_db.models import User, Post

from sqlalchemy import select
from sqlalchemy.orm import load_only, Session, selectinload

from sql_db import models as sql_models
from mysql_seeder import transaction


@transaction
def seed_users(session: Session = None):
    base_stmt = select(sql_models.User).options(
        load_only(
            sql_models.User.id,
            sql_models.User.name,
        ),
    )

    offset = 0
    step = 100

    while True:
        stmt = base_stmt.offset(offset).limit(step)

        if not (users := session.scalars(stmt).all()):
            break

        def _generate_users():
            for u in users:
                yield User(sql_id=u.id, name=u.name)

        query: QuerySet = User.objects
        query.insert(list(_generate_users()), load_bulk=False)

        print(f"{offset + len(users)} created...")

        offset += step

    print("User seeding complete.")


@transaction
def seed_posts(session: Session = None):
    base_stmt = select(sql_models.Post).options(
        selectinload(sql_models.Post.likes),
        selectinload(sql_models.Post.tags),
        selectinload(sql_models.Post.comments).options(
            selectinload(sql_models.Comment.likes),
        ),
    )
    offset = 0
    step = 20

    while True:
        stmt = base_stmt.offset(offset).limit(step)

        if not (posts := session.scalars(stmt).all()):
            break

        user_ids = chain(
            (p.user_id for p in posts),
            (like.user_id for p in posts for like in p.likes),
            (like.user_id for p in posts for c in p.comments for like in c.likes),
        )

        users: Sequence[User] = (
            User.objects(sql_id__in=set(user_ids)).only("id", "sql_id").all()
        )
        users_map = {u.sql_id: u.id for u in users}

        def _generate_post_comments(post: sql_models.Post):
            yield from (
                Post.Comment(
                    user=users_map[c.user_id],
                    body=c.body,
                    likes=list(users_map[like.user_id] for like in c.likes),
                    created_at=c.created_at,
                )
                for c in post.comments
            )

        def _generate_post():
            for p in posts:
                yield Post(
                    sql_id=p.id,
                    user=users_map[p.user_id],
                    title=p.title,
                    body=p.body,
                    views=p.views,
                    likes=[users_map[u.user_id] for u in p.likes],
                    comments=list(_generate_post_comments(p)),
                    tags=[tag.name for tag in p.tags],
                    created_at=p.created_at,
                )

        query: QuerySet = Post.objects
        query.insert(list(_generate_post()))

        print(f"{offset + len(posts)} posts created...")

        offset += step

    print("Post seeding complete.")


def seed():
    seed_users()
    seed_posts()
