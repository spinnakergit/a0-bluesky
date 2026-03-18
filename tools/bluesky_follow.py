from helpers.tool import Tool, Response


class BlueskyFollow(Tool):
    """Follow/unfollow users and list follows on Bluesky."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "followers")
        handle = self.args.get("handle", "")
        max_results = int(self.args.get("max_results", "50"))

        from plugins.bluesky.helpers.bluesky_auth import get_bluesky_config
        config = get_bluesky_config(self.agent)
        from plugins.bluesky.helpers.bluesky_client import BlueskyClient
        client = BlueskyClient(config)

        try:
            if action == "follow":
                if not handle:
                    return Response(message="Error: 'handle' is required for follow.", break_loop=False)
                from plugins.bluesky.helpers.sanitize import validate_handle
                handle = validate_handle(handle)
                self.set_progress(f"Following @{handle}...")
                # Resolve handle to DID first
                profile = await client.get_profile(handle)
                if profile.get("error"):
                    return Response(
                        message=f"Error looking up user: {profile.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                did = profile.get("did", "")
                if not did:
                    return Response(message=f"Could not resolve @{handle} to a DID.", break_loop=False)
                result = await client.follow(did)
                if result.get("error"):
                    return Response(
                        message=f"Error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                return Response(message=f"Now following @{handle}.", break_loop=False)

            elif action == "unfollow":
                uri = self.args.get("uri", "")
                if not uri:
                    return Response(
                        message="Error: 'uri' is required for unfollow (the follow record URI).",
                        break_loop=False,
                    )
                self.set_progress("Unfollowing...")
                result = await client.unfollow(uri)
                if result.get("error"):
                    return Response(
                        message=f"Error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                return Response(message="Unfollowed successfully.", break_loop=False)

            elif action == "followers":
                actor = handle if handle else None
                self.set_progress("Fetching followers...")
                result = await client.get_followers(actor, limit=max_results)
                if result.get("error"):
                    return Response(
                        message=f"Error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                followers = result.get("followers", [])
                if not followers:
                    return Response(message="No followers found.", break_loop=False)
                lines = [f"Followers ({len(followers)}):"]
                for f in followers:
                    fh = f.get("handle", "unknown")
                    fd = f.get("displayName", "")
                    entry = f"@{fh}"
                    if fd:
                        entry = f"{fd} (@{fh})"
                    lines.append(f"  {entry}")
                return Response(message="\n".join(lines), break_loop=False)

            elif action == "following":
                actor = handle if handle else None
                self.set_progress("Fetching following...")
                result = await client.get_follows(actor, limit=max_results)
                if result.get("error"):
                    return Response(
                        message=f"Error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                follows = result.get("follows", [])
                if not follows:
                    return Response(message="Not following anyone.", break_loop=False)
                lines = [f"Following ({len(follows)}):"]
                for f in follows:
                    fh = f.get("handle", "unknown")
                    fd = f.get("displayName", "")
                    entry = f"@{fh}"
                    if fd:
                        entry = f"{fd} (@{fh})"
                    lines.append(f"  {entry}")
                return Response(message="\n".join(lines), break_loop=False)

            else:
                return Response(
                    message=f"Error: Unknown action '{action}'. Use: follow, unfollow, followers, following.",
                    break_loop=False,
                )
        except ValueError as e:
            return Response(message=f"Validation error: {e}", break_loop=False)
        finally:
            await client.close()
