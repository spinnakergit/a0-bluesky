from helpers.tool import Tool, Response


class BlueskyRead(Tool):
    """Read posts, timelines, and user feeds from Bluesky."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "timeline")
        uri = self.args.get("uri", "")
        handle = self.args.get("handle", "")
        max_results = int(self.args.get("max_results", "20"))

        from plugins.bluesky.helpers.bluesky_auth import get_bluesky_config
        config = get_bluesky_config(self.agent)
        from plugins.bluesky.helpers.bluesky_client import BlueskyClient
        client = BlueskyClient(config)

        try:
            if action == "post":
                if not uri:
                    return Response(message="Error: 'uri' is required to read a post.", break_loop=False)
                from plugins.bluesky.helpers.sanitize import validate_at_uri
                try:
                    uri = validate_at_uri(uri)
                except ValueError as e:
                    return Response(message=f"Validation error: {e}", break_loop=False)
                self.set_progress("Fetching post...")
                result = await client.get_post_thread(uri, depth=0)
                if result.get("error"):
                    return Response(
                        message=f"Error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                post = result.get("thread", {}).get("post", {})
                if not post:
                    return Response(message="Post not found.", break_loop=False)
                from plugins.bluesky.helpers.sanitize import format_post
                return Response(message=format_post(post), break_loop=False)

            elif action == "thread":
                if not uri:
                    return Response(message="Error: 'uri' is required to read a thread.", break_loop=False)
                from plugins.bluesky.helpers.sanitize import validate_at_uri
                uri = validate_at_uri(uri)
                self.set_progress("Fetching thread...")
                result = await client.get_post_thread(uri, depth=10)
                if result.get("error"):
                    return Response(
                        message=f"Error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                thread = result.get("thread", {})
                posts = self._flatten_thread(thread)
                if not posts:
                    return Response(message="No posts found in thread.", break_loop=False)
                from plugins.bluesky.helpers.sanitize import format_posts
                return Response(
                    message=f"Thread ({len(posts)} posts):\n\n{format_posts(posts)}",
                    break_loop=False,
                )

            elif action == "user_posts":
                if not handle:
                    return Response(message="Error: 'handle' is required for user_posts.", break_loop=False)
                from plugins.bluesky.helpers.sanitize import validate_handle
                try:
                    handle = validate_handle(handle)
                except ValueError as e:
                    return Response(message=f"Validation error: {e}", break_loop=False)
                self.set_progress(f"Fetching posts from @{handle}...")
                result = await client.get_author_feed(handle, limit=max_results)
                if result.get("error"):
                    return Response(
                        message=f"Error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                feed = result.get("feed", [])
                if not feed:
                    return Response(message=f"No posts found from @{handle}.", break_loop=False)
                posts = [item.get("post", {}) for item in feed]
                from plugins.bluesky.helpers.sanitize import format_posts
                return Response(
                    message=f"Posts from @{handle} ({len(posts)}):\n\n{format_posts(posts)}",
                    break_loop=False,
                )

            elif action == "timeline":
                self.set_progress("Fetching timeline...")
                result = await client.get_timeline(limit=max_results)
                if result.get("error"):
                    return Response(
                        message=f"Error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                feed = result.get("feed", [])
                if not feed:
                    return Response(message="Timeline is empty.", break_loop=False)
                posts = [item.get("post", {}) for item in feed]
                from plugins.bluesky.helpers.sanitize import format_posts
                return Response(
                    message=f"Timeline ({len(posts)} posts):\n\n{format_posts(posts)}",
                    break_loop=False,
                )

            else:
                return Response(
                    message=f"Error: Unknown action '{action}'. Use: post, thread, user_posts, timeline.",
                    break_loop=False,
                )
        except ValueError as e:
            return Response(message=f"Validation error: {e}", break_loop=False)
        finally:
            await client.close()

    def _flatten_thread(self, thread: dict) -> list:
        """Flatten a thread tree into a list of posts."""
        posts = []
        post = thread.get("post")
        if post:
            posts.append(post)
        replies = thread.get("replies", [])
        for reply in replies:
            posts.extend(self._flatten_thread(reply))
        return posts
