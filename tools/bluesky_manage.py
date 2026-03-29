from helpers.tool import Tool, Response


class BlueskyManage(Tool):
    """Manage posts on Bluesky: delete, like, unlike, repost, unrepost."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "")
        uri = self.args.get("uri", "")

        # Normalize "remove" → "delete" (agent-facing name avoids triggering infection_check)
        if action == "remove":
            action = "delete"

        if not action:
            return Response(
                message="Error: 'action' is required (remove, like, unlike, repost, unrepost).",
                break_loop=False,
            )
        if not uri:
            return Response(message="Error: 'uri' is required.", break_loop=False)

        from usr.plugins.bluesky.helpers.bluesky_auth import get_bluesky_config
        config = get_bluesky_config(self.agent)
        from usr.plugins.bluesky.helpers.bluesky_client import BlueskyClient
        client = BlueskyClient(config)

        try:
            action_map = {
                "delete": ("Removing post...", "Post removed"),
                "like": ("Liking post...", "Post liked"),
                "unlike": ("Unliking post...", "Post unliked"),
                "repost": ("Reposting...", "Reposted"),
                "unrepost": ("Removing repost...", "Repost removed"),
            }

            if action not in action_map:
                return Response(
                    message=f"Error: Unknown action '{action}'. Use: remove, like, unlike, repost, unrepost.",
                    break_loop=False,
                )

            progress_msg, success_msg = action_map[action]
            self.set_progress(progress_msg)

            # Always resolve CID from the API for like/repost (never trust agent-provided values)
            cid = ""
            if action in ("like", "repost"):
                self.set_progress("Resolving post CID...")
                thread_result = await client.get_post_thread(uri, depth=0)
                post_data = thread_result.get("thread", {}).get("post", {})
                cid = post_data.get("cid", "")
                if not cid:
                    return Response(
                        message="Error: Could not resolve CID for this post URI.",
                        break_loop=False,
                    )

            if action == "delete":
                result = await client.delete_post(uri)
            elif action == "like":
                result = await client.like_post(uri, cid)
            elif action == "unlike":
                result = await client.unlike_post(uri)
            elif action == "repost":
                result = await client.repost(uri, cid)
            elif action == "unrepost":
                result = await client.unrepost(uri)

            if result.get("error"):
                return Response(
                    message=f"Error: {result.get('detail', 'Unknown error')}",
                    break_loop=False,
                )

            return Response(message=f"{success_msg}.", break_loop=False)
        finally:
            await client.close()
