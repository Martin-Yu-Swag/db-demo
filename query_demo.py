"""
Goal:
Get posts (along with their author id and name) published in June,
and find top views, top likes, top comments posts by each tag.

{
    "tag_1_name": {
        "posts": [
            {"title": "", "body": "", "author": "", "views"...},
        ],
        "best_view": {"title": "", "body": "", "author": "", "views"...},
        "best_like": {"title": "", "body": "", "author": "", "views"...},
        "best_comment": {"title": "", "body": "", "author": "", "views"...},
    },
    "tag_2_name": {}...
}
"""

from datetime import datetime


def sql_query():
    from sql_db.models import Tag, Post, PostLike, Comment
    from sql_db.db_config import engine
    from sqlalchemy import select, and_, func
    from sqlalchemy.orm import (
        selectinload,
        Session,
        load_only,
        with_loader_criteria,
        joinedload,
    )

    session = Session(engine)

    # Step 1. collect tags and there related posts
    stmt = (
        select(Tag)
        .order_by(Tag.name.asc())
        .options(
            load_only(Tag.id, Tag.name),
            selectinload(Tag.posts).options(
                load_only(Post.id, Post.title, Post.views, raiseload=True),
                joinedload(Post.user),
            ),
            with_loader_criteria(
                Post,
                and_(
                    Post.created_at >= datetime(2025, 6, 1),
                    Post.created_at <= datetime(2025, 6, 30),
                ),
            ),
        )
    )
    tags = session.scalars(stmt).all()

    post_ids = set(post.id for tag in tags for post in tag.posts)

    # Step 2. collect Post likes count
    stmt = (
        select(PostLike.post_id, func.count(PostLike.id))
        .select_from(PostLike)
        .where(PostLike.post_id.in_(post_ids))
        .group_by(PostLike.post_id)
    )
    results = session.execute(stmt).all()
    post_like_cnt = {result[0]: result[1] for result in results}

    # Step 3. collect Post comment count
    stmt = (
        select(Comment.post_id, func.count(Comment.id))
        .select_from(Comment)
        .where(Comment.post_id.in_(post_ids))
        .group_by(Comment.post_id)
    )
    results = session.execute(stmt).all()
    post_cmt_cnt = {result[0]: result[1] for result in results}

    # Step 4. organize data and return
    def _collect_tag_data(tag: Tag):
        posts = [
            {
                "id": post.id,
                "title": post.title,
                "views": post.views,
                "author": {
                    "id": post.user.id,
                    "name": post.user.name,
                },
                "like_count": post_like_cnt.get(post.id, 0),
                "comment_count": post_cmt_cnt.get(post.id, 0),
            }
            for post in tag.posts
        ]

        return {
            "posts": posts,
            "best_view": max(posts, key=lambda p: p["views"]),
            "best_like": max(posts, key=lambda p: p["like_count"]),
            "best_comment": max(posts, key=lambda p: p["comment_count"]),
        }

    return {tag.name: _collect_tag_data(tag) for tag in tags}


def mongo_query():
    import mongo_db  # noqa: F401
    from mongo_db.models import Post

    def _stages():
        # fmt: off
        yield {"$match": {
            "created_at": {
                "$gte": datetime(2025, 6, 1),
                "$lte": datetime(2025, 6, 30),
            },
        }}
        yield {"$project": {
            "_id": False,
            "id": "$sql_id",
            "title": True,
            "tags": True,
            "user": True,
            "views": True,
            "like_count": {"$size": "$likes"},
            "comment_count": {"$size": "$comments"},
        }}
        yield {"$lookup": {
            "from": "users",
            "localField": "user",
            "foreignField": "_id",
            "as": "user",
        }}
        yield {"$addFields": {
            "user": {"$first": "$user"},
        }}
        yield {"$addFields": {
            "author": {
                "id": "$user.sql_id",
                "name": "$user.name",
            },
        }}
        yield {"$unset": "user"}
        yield {"$unwind": "$tags"}
        yield {"$group": {
            "_id": "$tags",
            "posts": {"$push": "$$ROOT"},
        }}
        yield {"$unset": "posts.tags"}
        yield {"$addFields": {
            "best_view": {"$reduce": {
                "input": "$posts",
                "initialValue": {"views": -1},
                "in": {"$cond": {
                    "if": {"$gt": ["$$this.views", "$$value.views"]},
                    "then": "$$this",
                    "else": "$$value",
                }},
            }},
            "best_like": {"$reduce": {
                "input": "$posts",
                "initialValue": {"like_count": -1},
                "in": {"$cond": {
                    "if": {"$gt": ["$$this.like_count", "$$value.like_count"]},
                    "then": "$$this",
                    "else": "$$value",
                }},
            }},
            "best_comment": {"$reduce": {
                "input": "$posts",
                "initialValue": {"comment_count": -1},
                "in": {"$cond": {
                    "if": {"$gt": ["$$this.comment_count","$$value.comment_count"]},
                    "then": "$$this",
                    "else": "$$value",
                }},
            }},
        }}
        yield {"$sort": {"_id": 1}}
        # fmt: on

    return {
        doc["_id"]: {
            "posts": doc["posts"],
            "best_view": doc["best_view"],
            "best_like": doc["best_like"],
            "best_comment": doc["best_comment"],
        }
        for doc in Post.objects.aggregate(_stages())
    }


sql_results = sql_query()
mongo_results = mongo_query()

for (sql_tag, sql_data), (mongo_tag, mongo_data) in zip(
    sql_results.items(), mongo_results.items()
):
    assert sql_tag == mongo_tag
    assert sql_data["best_view"] == mongo_data["best_view"]
    assert sql_data["best_like"] == mongo_data["best_like"]
    assert sql_data["best_comment"] == mongo_data["best_comment"]

print("Query comparison done.")
