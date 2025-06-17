from datetime import datetime

from sqlalchemy import String, ForeignKey, TIMESTAMP, Text, UniqueConstraint, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), comment="UTC timezone")
    


class User(Base):
    __tablename__ = 'users'

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    posts: Mapped[list['Post']] = relationship(back_populates='user')
    post_likes: Mapped[list['PostLike']] = relationship(back_populates='user')
    comments: Mapped[list['Comment']] = relationship(back_populates='user')
    comment_likes: Mapped[list['CommentLike']] = relationship(back_populates='user')


class Post(Base):
    __tablename__ = 'posts'

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped['User'] = relationship(back_populates='posts')
    comments: Mapped[list['Comment']] = relationship(back_populates='post')
    likes: Mapped[list['PostLike']] = relationship(back_populates='post')

    tags: Mapped[list['Post']] = relationship(
        secondary='post_tag',
        primaryjoin="PostTag.tag_id == Tag.id",
        secondaryjoin="PostTag.post_id == Post.id",
        back_populates="posts",
    )



class PostLike(Base):
    __tablename__ = 'post_likes'
    __table_args__ = (
        UniqueConstraint('user_id', 'post_id'),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False)

    user: Mapped['User'] = relationship(back_populates='post_likes')
    post: Mapped['Post'] = relationship(back_populates='likes')


class Comment(Base):
    __tablename__ = 'post_comments'

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped['User'] = relationship(back_populates='comments')
    post: Mapped['Post'] = relationship(back_populates='comments')
    likes: Mapped[list['CommentLike']] = relationship(back_populates='comment')


class CommentLike(Base):
    __tablename__ = 'comment_likes'
    __table_args__ = (
        UniqueConstraint('user_id', 'comment_id'),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    comment_id: Mapped[int] = mapped_column(ForeignKey("post_comments.id"), nullable=False)

    user: Mapped['User'] = relationship(back_populates='comment_likes')
    comment: Mapped['Comment'] = relationship(back_populates='likes')


class Tag(Base):
    __tablename__ = 'tags'

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    posts: Mapped[list['Post']] = relationship(
        secondary='post_tag',
        primaryjoin="PostTag.post_id == Post.id",
        secondaryjoin="PostTag.tag_id == Tag.id",
        back_populates="tags",
    )


class PostTag(Base):
    __tablename__ = 'post_tag'
    __table_args__ = (
        UniqueConstraint('post_id', 'tag_id'),
    )

    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)
