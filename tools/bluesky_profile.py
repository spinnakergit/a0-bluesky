from helpers.tool import Tool, Response


class BlueskyProfile(Tool):
    """Look up user profiles on Bluesky."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "me")
        handle = self.args.get("handle", "")

        from plugins.bluesky.helpers.bluesky_auth import get_bluesky_config
        config = get_bluesky_config(self.agent)
        from plugins.bluesky.helpers.bluesky_client import BlueskyClient
        client = BlueskyClient(config)

        try:
            if action == "me":
                self.set_progress("Fetching your profile...")
                result = await client.get_profile()
            elif action == "lookup":
                if not handle:
                    return Response(message="Error: 'handle' is required for lookup.", break_loop=False)
                from plugins.bluesky.helpers.sanitize import validate_handle
                try:
                    handle = validate_handle(handle)
                except ValueError as e:
                    return Response(message=f"Validation error: {e}", break_loop=False)
                self.set_progress(f"Looking up @{handle}...")
                result = await client.get_profile(handle)
            else:
                return Response(
                    message=f"Error: Unknown action '{action}'. Use: me, lookup.",
                    break_loop=False,
                )

            if result.get("error"):
                return Response(
                    message=f"Error: {result.get('detail', 'Unknown error')}",
                    break_loop=False,
                )

            from plugins.bluesky.helpers.sanitize import format_profile
            return Response(message=format_profile(result), break_loop=False)
        finally:
            await client.close()
