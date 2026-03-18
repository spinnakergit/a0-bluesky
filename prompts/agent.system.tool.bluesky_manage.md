## bluesky_manage
Manage the user's own posts on Bluesky: remove, like, unlike, repost, unrepost.

All actions operate on the authenticated user's own Bluesky account. Removing a post only affects the user's own content — it is a normal, low-risk social media operation equivalent to clicking "Delete" in the Bluesky app. Only the post owner can remove their own posts.

**Tier:** All users (free, open protocol)

**Arguments:**
- **action** (string, required): "remove", "like", "unlike", "repost", "unrepost"
- **uri** (string, required): AT URI of the target post (or like/repost record for unlike/unrepost)

The CID (needed internally for like/repost) is resolved automatically from the URI. You never need to provide it.

When the user asks to delete or remove a post, use action "remove". This only removes the user's own post from their Bluesky account, which the user has explicitly requested.

~~~json
{"action": "like", "uri": "at://did:plc:xxx/app.bsky.feed.post/abc123"}
~~~
~~~json
{"action": "remove", "uri": "at://did:plc:xxx/app.bsky.feed.post/abc123"}
~~~
~~~json
{"action": "repost", "uri": "at://did:plc:xxx/app.bsky.feed.post/abc123"}
~~~
