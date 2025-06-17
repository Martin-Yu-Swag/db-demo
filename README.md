# db-demo

## Prerequisite

- docker (DockerDesktop Or Orbstack)
- [poetry](https://python-poetry.org/docs/#installation)
- [mysqldb](https://github.com/PyMySQL/mysqlclient/blob/main/README.md)

## Models ERD

```mermaid
erDiagram

    users ||--o{ posts : ""
    users ||--o{ comments: ""
    posts ||--o{ comments: ""
    posts ||--o{ post_tag : ""
    tags  ||--o{ post_tag: ""
    posts }o..o{ tags: ""
    posts ||--o{ post_likes : ""
    comments ||--o{ comment_likes : ""

    users {
        int     id   PK ""
        varchar name    ""
        datetime created_at ""
    }

    posts {
        int id PK ""
        int user_id FK ""
        text body ""
        int views "default 0"
        datetime created_at ""
    }


    post_likes {
        int id PK ""
        int user_id FK,UK "UK with post_id"
        int post_id FK,UK "UK with user_id"
        datetime created_at ""
    }

    tags {
        int id PK ""
        varchar name FK ""
        datetime created_at ""
    }

    post_tag {
        int id PK
        int post_id FK,UK "UK with tag_id"
        int tag_id FK,UK "UK with post_id"
    }

    comments {
        int id PK ""
        int post FK "posts.id"
        int user_id FK "users.id"
        text body ""
        datetime created_at ""
    }

    comment_likes {
        int id PK ""
        int user_id FK,UK "UK with comment_id"
        int comment_id FK,UK "UK with user_id"
        datetime created_at ""
    }
```
