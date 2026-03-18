## bluesky_post
Post, reply, and quote on Bluesky.

**Tier:** All users (free, open protocol)

**Arguments:**
- **action** (string): "post" (default), "reply", or "quote"
- **text** (string, required): Post content (max 300 graphemes)
- **uri** (string): AT URI of post to reply to or quote
- **cid** (string): CID of post to quote (required for quote posts)

~~~json
{"action": "post", "text": "Hello Bluesky!"}
~~~
~~~json
{"action": "reply", "text": "Great point!", "uri": "at://did:plc:xxx/app.bsky.feed.post/abc123"}
~~~
~~~json
{"action": "quote", "text": "Check this out:", "uri": "at://did:plc:xxx/app.bsky.feed.post/abc123", "cid": "bafyrei..."}
~~~
