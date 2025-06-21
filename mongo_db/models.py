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
    sql_id = IntField(min_value=1, required=True, unique=True)
    name = StringField(max_length=100, required=True)
    created_at = DateTimeField(default=datetime.now)

    meta = {
        "collection": "users",
    }


class Post(Document):
    class Comment(EmbeddedDocument):
        user = LazyReferenceField("User", required=True)
        body = StringField(required=True)
        likes = ListField(field=ObjectIdField())
        created_at = DateTimeField(default=datetime.now)

    sql_id = IntField(min_value=1, required=True, unique=True)
    user = LazyReferenceField("User", required=True)
    title = StringField(max_length=200, required=True)
    body = StringField(required=True)
    views = IntField(min_value=0, default=0)
    likes = ListField(field=ObjectIdField())
    comments = EmbeddedDocumentListField(Comment)
    tags = ListField(StringField(max_length=50))
    created_at = DateTimeField(default=datetime.now)

    meta = {
        "collection": "posts",
        "index_background": True,
        "indexes": [
            {"fields": ["tags"]},
        ],
    }
