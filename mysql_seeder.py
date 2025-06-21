from functools import wraps
from datetime import datetime, timedelta
from collections.abc import Sequence
from faker import Faker
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, load_only

from sql_db.db_config import engine
from sql_db.models import Base, User, Tag, Post, PostLike, PostTag, Comment, CommentLike

fake = Faker(locale="zh_tw")

tag_names = (
    "科幻",
    "教育",
    "兩性",
    "科技",
    "言情",
    "家庭",
    "職場",
    "心理",
    "文學",
    "學習",
    "個人成長",
    "寵物",
    "八卦",
    "時事",
    "經濟",
    "商業",
    "電影",
    "遊戲",
    "美食",
    "旅遊",
    "科普",
)


def migrate_models():
    Base.metadata.create_all(engine)


def drop_models():
    Base.metadata.drop_all(engine)


def transaction(func):
    @wraps(func)
    def _inner(*args, **kwargs):
        with Session(engine) as session:
            func(*args, **kwargs, session=session)

    return _inner


@transaction
def generate_users(num: int, session: Session = None):
    for idx in range(0, num, 100):
        gen_num = 100 if num - idx > 100 else num - idx
        users = (User(name=fake.name()) for _ in range(gen_num))
        session.add_all(users)
        session.commit()

        print(f"{(idx + 100)} users created...")

    print("User generation complete.")


@transaction
def generate_tags(session: Session = None):
    for name in tag_names:
        try:
            session.add(Tag(name=name))
            session.commit()
        except IntegrityError:
            session.rollback()
            continue

    print("Tag generation complete.")
    return


@transaction
def generate_posts(
    user_ids: Sequence[int] = None,
    max_post_num_for_each_user: int = 10,
    session: Session = None,
):
    if not user_ids:
        user_ids = session.scalars(select(User.id)).all()

    now = datetime.now()

    def _generate_posts(
        start_from: datetime,
        end_at: datetime,
    ):
        max_num = max_post_num_for_each_user
        for uid in user_ids:
            for _ in range(fake.random_int(3, max_num)):
                yield Post(
                    user_id=uid,
                    title=fake.sentence(),
                    body=fake.text(),
                    views=fake.random_int(10, 1000),
                    created_at=fake.date_between(start_from, end_at),
                )

    # Generate post across 3 month
    for idx in range(3, 0, -1):
        start = now - timedelta(days=30 * idx)
        end = now - timedelta(days=30 * (idx - 1))

        posts = sorted(
            _generate_posts(start, end),
            key=lambda post: post.created_at,
        )

        session.add_all(posts)
        session.commit()

        print(
            f"{len(posts)} posts from {start.isoformat()} to {end.isoformat()} created..."
        )

    print("Post generation complete.")


@transaction
def generate_post_likes(session: Session = None):
    user_ids = session.scalars(select(User.id)).all()

    def _generate_likes(
        posts: Sequence[Post],
    ):
        for p in posts:
            max_cnt = min(p.views, len(user_ids))
            cnt = fake.random_int(0, max_cnt)
            like_users = fake.random_sample(user_ids, length=cnt)
            yield from (
                PostLike(
                    user_id=uid,
                    post_id=p.id,
                    created_at=fake.date_between(p.created_at, datetime.now()),
                )
                for uid in like_users
            )

    post_stmt = (
        select(Post)
        .options(load_only(Post.id, Post.views, Post.created_at, raiseload=True))
        .order_by(Post.id.asc())
    )
    offset = 0
    step = 20

    while True:
        stmt = post_stmt.offset(offset).limit(step)
        posts = session.scalars(stmt).all()

        if not len(posts):
            break

        session.add_all(_generate_likes(posts))
        session.commit()
        print(f"Likes of {offset + len(posts)} posts created...")

        offset += step

    print("PostLike generation complete.")


@transaction
def generate_post_tags(session: Session):
    tag_ids = session.scalars(select(Tag.id)).all()

    def _generate_tags(
        posts: Sequence[Post],
    ):
        for p in posts:
            cnt = fake.random_int(2, 5)
            yield from (
                PostTag(
                    post_id=p.id,
                    tag_id=tag_id,
                    created_at=p.created_at,
                )
                for tag_id in fake.random_sample(tag_ids, cnt)
            )

    post_stmt = (
        select(Post)
        .options(load_only(Post.id, Post.created_at, raiseload=True))
        .order_by(Post.id.asc())
    )
    offset = 0
    step = 50

    while True:
        stmt = post_stmt.offset(offset).limit(step)
        posts = session.scalars(stmt).all()

        if not len(posts):
            break

        session.add_all(_generate_tags(posts))
        session.commit()
        print(f"Tags of {offset + len(posts)} posts created...")

        offset += step

    print("PostTag generation complete.")


@transaction
def generate_post_comments(session: Session):
    user_ids = session.scalars(select(User.id)).all()

    def _generate_comments(
        posts: Sequence[Post],
    ):
        for p in posts:
            max_cnt = min(30, len(user_ids))
            cnt = fake.random_int(0, max_cnt)
            comment_users = fake.random_choices(user_ids, length=cnt)
            yield from (
                Comment(
                    post_id=p.id,
                    user_id=uid,
                    body=fake.sentence(),
                    created_at=fake.date_between(p.created_at, datetime.now()),
                )
                for uid in comment_users
            )

    post_stmt = (
        select(Post)
        .options(load_only(Post.id, Post.created_at, raiseload=True))
        .order_by(Post.id.asc())
    )
    offset = 0
    step = 10

    while True:
        stmt = post_stmt.offset(offset).limit(step)
        posts = session.scalars(stmt).all()

        if not len(posts):
            break

        session.add_all(_generate_comments(posts))
        session.commit()
        print(f"Comments of {offset + len(posts)} posts created...")

        offset += step

    print("PostComment generation complete.")


@transaction
def generate_post_comment_likes(session: Session = None):
    user_ids = session.scalars(select(User.id)).all()

    def _generate_comment_likes(
        comments: Sequence[Comment],
    ):
        for c in comments:
            # only 10% of comments will have likes
            if not fake.random_int(1, 10) == 1:
                continue

            cnt = fake.random_int(1, len(user_ids))
            yield from (
                CommentLike(
                    user_id=uid,
                    comment_id=c.id,
                    created_at=fake.date_between(c.created_at, datetime.now()),
                )
                for uid in fake.random_sample(user_ids, length=cnt)
            )

    stmt = (
        select(Comment)
        .options(load_only(Comment.id, Comment.created_at, raiseload=True))
        .order_by(Comment.id.asc())
    )
    offset = 0
    step = 1000

    while True:
        stmt = stmt.offset(offset).limit(step)
        comments = session.scalars(stmt).all()

        if not len(comments):
            break

        session.add_all(_generate_comment_likes(comments))
        session.commit()
        print(f"CommentLike of {offset + len(comments)} comments created...")

        offset += step

    print("CommentLike generation complete.")


def build_and_seed():
    drop_models()
    migrate_models()
    generate_tags()
    generate_users(100)
    generate_posts()
    generate_post_tags()
    generate_post_likes()
    generate_post_comments()
    generate_post_comment_likes()
    return


# build_and_seed()
