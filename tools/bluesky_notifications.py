from helpers.tool import Tool, Response


class BlueskyNotifications(Tool):
    """Read notifications from Bluesky (likes, reposts, follows, mentions, replies)."""

    async def execute(self, **kwargs) -> Response:
        max_results = int(self.args.get("max_results", "30"))

        from usr.plugins.bluesky.helpers.bluesky_auth import get_bluesky_config
        config = get_bluesky_config(self.agent)
        from usr.plugins.bluesky.helpers.bluesky_client import BlueskyClient
        client = BlueskyClient(config)

        try:
            self.set_progress("Fetching notifications...")
            result = await client.get_notifications(limit=max_results)

            if result.get("error"):
                return Response(
                    message=f"Error: {result.get('detail', 'Unknown error')}",
                    break_loop=False,
                )

            notifications = result.get("notifications", [])
            if not notifications:
                return Response(message="No notifications.", break_loop=False)

            from usr.plugins.bluesky.helpers.sanitize import format_notification
            lines = [f"Notifications ({len(notifications)}):\n"]
            for notif in notifications:
                lines.append(format_notification(notif))

            return Response(message="\n".join(lines), break_loop=False)
        finally:
            await client.close()
