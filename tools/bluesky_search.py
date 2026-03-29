from helpers.tool import Tool, Response


class BlueskySearch(Tool):
    """Search posts and users on Bluesky."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "posts")
        query = self.args.get("query", "")
        max_results = int(self.args.get("max_results", "25"))
        sort = self.args.get("sort", "latest")

        if not query:
            return Response(message="Error: 'query' is required.", break_loop=False)
        if len(query) > 512:
            return Response(message="Error: Query too long (max 512 characters).", break_loop=False)
        if sort not in ("latest", "top"):
            return Response(message="Error: 'sort' must be 'latest' or 'top'.", break_loop=False)

        from usr.plugins.bluesky.helpers.bluesky_auth import get_bluesky_config
        config = get_bluesky_config(self.agent)
        from usr.plugins.bluesky.helpers.bluesky_client import BlueskyClient
        client = BlueskyClient(config)

        try:
            if action == "posts":
                self.set_progress(f"Searching posts: {query[:50]}...")
                result = await client.search_posts(query, limit=max_results, sort=sort)
                if result.get("error"):
                    return Response(
                        message=f"Error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                posts = result.get("posts", [])
                if not posts:
                    return Response(message=f"No posts found for: {query}", break_loop=False)
                from usr.plugins.bluesky.helpers.sanitize import format_posts
                return Response(
                    message=f"Found {len(posts)} post(s) for \"{query}\":\n\n{format_posts(posts)}",
                    break_loop=False,
                )

            elif action == "users":
                self.set_progress(f"Searching users: {query[:50]}...")
                result = await client.search_actors(query, limit=max_results)
                if result.get("error"):
                    return Response(
                        message=f"Error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                actors = result.get("actors", [])
                if not actors:
                    return Response(message=f"No users found for: {query}", break_loop=False)
                lines = [f"Found {len(actors)} user(s) for \"{query}\":\n"]
                for actor in actors:
                    handle = actor.get("handle", "unknown")
                    display = actor.get("displayName", "")
                    desc = actor.get("description", "")[:100]
                    followers = actor.get("followersCount", 0)
                    line = f"@{handle}"
                    if display:
                        line = f"{display} (@{handle})"
                    line += f" — {followers} followers"
                    if desc:
                        line += f"\n  {desc}"
                    lines.append(line)
                return Response(message="\n".join(lines), break_loop=False)

            else:
                return Response(
                    message=f"Error: Unknown action '{action}'. Use: posts, users.",
                    break_loop=False,
                )
        finally:
            await client.close()
