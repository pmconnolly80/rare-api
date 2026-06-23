# Sequence Diagram — User Creates a Post

> Traced from the source files. Key files involved:
> `PostCreate.js` · `CategoryManager.js` · `PostManager.js` · `api.js`
> `rareapi/urls.py` · `post_views.py` · `category_views.py` · PostgreSQL

```mermaid
sequenceDiagram
    actor User
    participant PC as PostCreate.js
    participant CM as CategoryManager.js
    participant PM as PostManager.js
    participant AJ as api.js
    participant URL as urls.py (router)
    participant CV as category_views.py
    participant PV as post_views.py
    participant DB as PostgreSQL

    Note over PC,DB: Phase 1 — Component mounts, categories are fetched

    PC->>CM: getCategories()
    CM->>AJ: authHeader()
    AJ-->>CM: {Authorization: "Token <localStorage>"}
    CM->>URL: GET /categories
    URL->>CV: category_list(request)
    CV->>DB: Category.objects.all()
    DB-->>CV: [category rows]
    CV-->>URL: Response(CategorySerializer, 200)
    URL-->>CM: JSON array of categories
    CM-->>PC: categories[]
    PC->>PC: setCategories(data) — populates dropdown

    Note over PC,DB: Phase 2 — User fills out form and clicks Save

    User->>PC: clicks Save button
    PC->>PC: handleSave(e) — reads titleRef, categoryRef, contentRef
    PC->>PM: createPost({title, category_id, content})
    PM->>AJ: authHeader()
    AJ-->>PM: {Authorization: "Token <localStorage>"}
    PM->>URL: POST /posts<br/>{title, category_id, content}
    URL->>PV: post_list(request) — method is POST
    PV->>DB: Category.objects.get(pk=category_id)
    DB-->>PV: category row (or DoesNotExist → 400)
    Note over PV: approved = request.user.is_staff<br/>Staff → True (auto-published)<br/>Non-staff → False (enters moderation queue)
    PV->>DB: Post.objects.create(user, category, title,<br/>content, image_url="", publication_date=today,<br/>approved=is_staff)
    DB-->>PV: new post row with id
    PV-->>URL: Response(PostDetailSerializer, 201)
    URL-->>PM: JSON post object {id, title, ...}
    PM-->>PC: post object

    Note over PC,DB: Phase 3 — Image upload (only if user attached a file)

    alt user attached an image file
        PC->>PC: reads fileRef.current.files[0]
        PC->>PC: builds FormData with image
        PC->>PM: uploadPostImage(post.id, formData)
        PM->>AJ: authHeader()
        AJ-->>PM: {Authorization: "Token <localStorage>"}
        PM->>URL: PUT /posts/{id}/image<br/>multipart FormData
        URL->>PV: upload_post_image(request, pk)
        PV->>PV: writes file to media/post_images/<br/>builds absolute URL
        PV->>DB: post.image_url = absolute_url<br/>post.save()
        DB-->>PV: updated post row
        PV-->>URL: Response({image_url}, 200)
        URL-->>PM: JSON {image_url}
        PM-->>PC: response
    end

    Note over PC: Phase 4 — Navigation

    PC->>User: navigate("/posts/{post.id}")
```

## Key points

| What | Where it happens |
|---|---|
| Auth token is attached | `api.js` → `authHeader()` reads `localStorage.getItem("auth_token")` and returns the header. Neither the component nor the manager constructs it. |
| `approved` is decided server-side | `post_views.py` line 33: `approved=request.user.is_staff`. The client never sends this field. |
| `publication_date` is always today | `post_views.py` sets it via `timezone.now().date()`. The client cannot schedule a future post. |
| Image upload is a second HTTP request | If a file is attached, `PostCreate.js` calls `uploadPostImage()` only after `createPost()` resolves. If the second call fails, the post exists without an image and no error is shown. |
| Category list is fetched on mount | `useEffect(() => { getCategories().then(setCategories) }, [])` in `PostCreate.js`. The form is rendered immediately but the dropdown is empty until this resolves. |
