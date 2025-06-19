from datetime import datetime
from mongoengine import (
    Document,
    StringField,
    LazyReferenceField,
    EmbeddedDocument,
    EmbeddedDocumentListField,
    IntField,
    ListField,
    ObjectIdField,
    DateTimeField,
)


class User(Document):
    name = StringField(max_length=100, required=True)
    created_at = DateTimeField(default=datetime.now)

    meta = {
        "collection": "users",
    }


class Post(Document):
    class Comment(EmbeddedDocument):
        user = LazyReferenceField("User", required=True)
        body = StringField(required=True)
        likes = ListField(field=ObjectIdField, unique=True)
        created_at = DateTimeField(default=datetime.now)

    user = LazyReferenceField("User", required=True)
    title = StringField(max_length=200, required=True)
    body = StringField(required=True)
    views = IntField(min_value=0, default=0)
    likes = ListField(field=ObjectIdField, unique=True)
    comments = EmbeddedDocumentListField(Comment)
    tags = ListField(StringField, unique=True)
    created_at = DateTimeField(default=datetime.now)

    meta = {
        "collection": "posts",
    }
