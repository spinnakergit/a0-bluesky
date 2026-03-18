## bluesky_search
Search posts and users on Bluesky.

**Tier:** All users (free, open protocol)

**Arguments:**
- **action** (string): "posts" (default) or "users"
- **query** (string, required): Search query
- **max_results** (string): Number of results (default: "25")
- **sort** (string): "latest" (default) or "top"

~~~json
{"action": "posts", "query": "AI agents", "sort": "top"}
~~~
~~~json
{"action": "users", "query": "machine learning"}
~~~
