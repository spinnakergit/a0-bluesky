## bluesky_follow
Follow/unfollow users and list follows on Bluesky.

**Tier:** All users (free, open protocol)

**Arguments:**
- **action** (string): "followers" (default), "following", "follow", "unfollow"
- **handle** (string): Handle to follow or whose followers/following to list
- **uri** (string): Follow record URI (for unfollow)
- **max_results** (string): Number of results (default: "50")

~~~json
{"action": "follow", "handle": "user.bsky.social"}
~~~
~~~json
{"action": "followers", "handle": "user.bsky.social"}
~~~
~~~json
{"action": "following"}
~~~
