## bluesky_read
Read posts, timelines, threads, and user feeds from Bluesky.

**Tier:** All users (free, open protocol)

**Arguments:**
- **action** (string): "timeline" (default), "post", "thread", "user_posts"
- **uri** (string): AT URI of post (for "post" and "thread" actions)
- **handle** (string): Bluesky handle (for "user_posts")
- **max_results** (string): Number of results (default: "20")

~~~json
{"action": "timeline"}
~~~
~~~json
{"action": "post", "uri": "at://did:plc:xxx/app.bsky.feed.post/abc123"}
~~~
~~~json
{"action": "user_posts", "handle": "user.bsky.social", "max_results": "10"}
~~~
