# Rare — Database Schema

> Generated from the model files in `rareapi/models/`. See that directory for the authoritative source.

```mermaid
erDiagram

    RareUser {
        int id PK
        string username
        string email
        string password
        string first_name
        string last_name
        bool is_staff
        bool is_active
        string bio
        string profile_image_url
        date created_on
    }

    Post {
        int id PK
        int user_id FK
        int category_id FK
        string title
        date publication_date
        string image_url
        text content
        bool approved
    }

    Category {
        int id PK
        string label
    }

    Tag {
        int id PK
        string label
    }

    Reaction {
        int id PK
        string label
        string image_url
    }

    Comment {
        int id PK
        int post_id FK
        int author_id FK
        string subject
        text content
        datetime created_on
    }

    PostTag {
        int id PK
        int post_id FK
        int tag_id FK
    }

    PostReaction {
        int id PK
        int user_id FK
        int post_id FK
        int reaction_id FK
    }

    Subscription {
        int id PK
        int follower_id FK
        int author_id FK
        date created_on
        datetime ended_on
    }

    DemotionQueue {
        int id PK
        string action
        int admin_id FK
        int approver_one_id FK
    }

    RareUser ||--o{ Post : "writes"
    Category ||--o{ Post : "groups"
    Post ||--o{ Comment : "has"
    RareUser ||--o{ Comment : "authors"
    Post ||--o{ PostTag : "tagged via"
    Tag ||--o{ PostTag : "applied via"
    Post ||--o{ PostReaction : "reacted to via"
    RareUser ||--o{ PostReaction : "reacts via"
    Reaction ||--o{ PostReaction : "used in"
    RareUser ||--o{ Subscription : "follows (follower)"
    RareUser ||--o{ Subscription : "followed by (author)"
    RareUser ||--o{ DemotionQueue : "initiates (admin)"
    RareUser ||--o{ DemotionQueue : "approves (approver_one)"
```

## Notes

- **RareUser** extends Django's built-in `AbstractUser`. The fields `username`, `email`, `password`, `first_name`, `last_name`, `is_staff`, and `is_active` are inherited — they are not declared in `rare_user.py` but do exist as database columns.
- **PostTag** and **PostReaction** are explicit join tables rather than Django `ManyToManyField` declarations. This gives the views direct ORM access to the join rows (e.g. to delete all tags for a post before replacing them).
- **Subscription.ended_on** is nullable. A subscription with `ended_on=NULL` is active; one with a value has been cancelled. Rows are never deleted — only soft-closed.
- **DemotionQueue** implements a two-admin voting system. `action` is a string key like `deactivate:42` or `demote:7`. A `unique_together` constraint on `(action, admin, approver_one)` prevents the same admin from voting twice. See `rareapi/services/admin_actions.py` for the full logic.
