# Rare — System Architecture

```mermaid
graph TD
    subgraph Browser["Browser (localhost:3000)"]
        UI["React App\n─────────────────\nCreate React App\nReact Router v6\nBulma CSS"]
        LS[("localStorage\n─────────────\nauth_token")]
    end

    subgraph Client["Client layer (rare-client/src/)"]
        MGR["Manager modules\n─────────────────\nPostManager.js\nCommentManager.js\nCategoryManager.js\n... one per entity"]
        API_JS["api.js\n─────────────────\nBase URL: localhost:8000\nauthHeader() helper"]
    end

    subgraph Django["Django REST API (localhost:8000)"]
        URLS["URL router\n─────────────────\nrareproject/urls.py\nrareapi/urls.py"]
        VIEWS["Views\n─────────────────\nFunction-based views\n@api_view + @permission_classes\none file per entity"]
        SVC["Services\n─────────────────\nadmin_actions.py\nTwo-admin voting logic"]
        SER["Serializers\n─────────────────\nPostDetailSerializer\nPostListSerializer\n... list + detail per model"]
        ORM["Django ORM\n─────────────────\npsycopg2 driver"]
    end

    subgraph Models["Models (rareapi/models/)"]
        M["RareUser · Post · Category\nTag · Reaction · Comment\nPostTag · PostReaction\nSubscription · DemotionQueue"]
    end

    subgraph Storage["Storage"]
        PG[("PostgreSQL 16\n─────────────────\nport 5432\nDocker container")]
        DISK[("Local filesystem\n─────────────────\nmedia/post_images/\nmedia/profile_images/")]
    end

    UI -- "reads/writes token" --> LS
    UI -- "calls" --> MGR
    MGR -- "uses" --> API_JS
    MGR -- "fetch() REST/JSON\nAuthorization: Token ..." --> URLS

    URLS -- "routes to" --> VIEWS
    VIEWS -- "complex admin actions" --> SVC
    VIEWS -- "serializes response" --> SER
    SER -- "reads" --> Models
    VIEWS -- "ORM queries\n.create() .get() .filter() .save()" --> ORM
    ORM -- "SQL via psycopg2" --> PG
    VIEWS -- "file writes\nopen(filepath, wb+)" --> DISK
    DISK -- "absolute URL stored in\nPost.image_url /\nRareUser.profile_image_url" --> ORM
```

## Component notes

| Component | What it is |
|---|---|
| **React App** | Single-page app bootstrapped with Create React App. Routing handled by React Router v6. No state management library — local `useState`/`useRef` only. |
| **Manager modules** | Thin `fetch()` wrappers, one file per entity. All auth headers assembled by `api.js`. No error handling — failed requests are silent. |
| **URL router** | Standard Django URL conf. `rareproject/urls.py` mounts all API routes under `/`; `rareapi/urls.py` defines every individual path. No trailing slashes. |
| **Views** | Function-based DRF views. Each function handles multiple HTTP methods via `if request.method`. Auth enforced by `@permission_classes([IsAuthenticated])`; admin-only paths check `request.user.is_staff` manually. |
| **Services** | `admin_actions.py` only. Implements two-admin approval for demoting or deactivating another admin — first call queues (202), second call executes (204). All other logic lives directly in views. |
| **Serializers** | Two per model: a slim `*ListSerializer` for collection endpoints and a full `*DetailSerializer` for single-resource and mutation responses. |
| **PostgreSQL** | Runs in Docker (see `docker-compose.yml`). Django ORM handles all reads and writes via `psycopg2`. |
| **Local filesystem** | Image uploads are written to disk with `open()`. URLs are absolute (`request.build_absolute_uri`), so they break on redeploy or behind a load balancer. |
