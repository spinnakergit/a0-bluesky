from helpers.tool import Tool, Response


class BlueskyThread(Tool):
    """Post multi-part threads on Bluesky."""

    async def execute(self, **kwargs) -> Response:
        posts_text = self.args.get("posts", "")
        separator = self.args.get("separator", "---")

        if not posts_text:
            return Response(message="Error: 'posts' is required. Provide thread posts separated by '---'.", break_loop=False)

        # Split into individual posts
        parts = [p.strip() for p in posts_text.split(separator) if p.strip()]
        if len(parts) < 2:
            return Response(
                message="Error: A thread needs at least 2 posts. Separate them with '---'.",
                break_loop=False,
            )
        if len(parts) > 25:
            return Response(message="Error: Thread too long (max 25 posts).", break_loop=False)

        from plugins.bluesky.helpers.sanitize import sanitize_post_text, validate_post_length
        for i, part in enumerate(parts):
            parts[i] = sanitize_post_text(part)
            ok, count = validate_post_length(parts[i])
            if not ok:
                return Response(
                    message=f"Post {i+1} is too long: {count}/300 graphemes.",
                    break_loop=False,
                )

        from plugins.bluesky.helpers.bluesky_auth import get_bluesky_config
        config = get_bluesky_config(self.agent)
        from plugins.bluesky.helpers.bluesky_client import BlueskyClient
        client = BlueskyClient(config)

        try:
            posted_uris = []
            root_uri = None
            root_cid = None
            parent_uri = None
            parent_cid = None

            from plugins.bluesky.helpers.sanitize import detect_facets

            for i, part in enumerate(parts):
                self.set_progress(f"Posting {i+1}/{len(parts)}...")

                reply_to = None
                if i > 0 and parent_uri and parent_cid:
                    reply_to = {
                        "root": {"uri": root_uri, "cid": root_cid},
                        "parent": {"uri": parent_uri, "cid": parent_cid},
                    }

                facets = detect_facets(part)
                result = await client.create_post(
                    text=part,
                    reply_to=reply_to,
                    facets=facets if facets else None,
                )

                if result.get("error"):
                    return Response(
                        message=f"Error posting part {i+1}: {result.get('detail', 'Unknown error')}. "
                        f"Posted {len(posted_uris)}/{len(parts)} parts.",
                        break_loop=False,
                    )

                new_uri = result.get("uri", "")
                new_cid = result.get("cid", "")
                posted_uris.append(new_uri)

                if i == 0:
                    root_uri = new_uri
                    root_cid = new_cid
                parent_uri = new_uri
                parent_cid = new_cid

            return Response(
                message=f"Thread posted successfully ({len(posted_uris)} posts).\nFirst post: {root_uri}",
                break_loop=False,
            )
        finally:
            await client.close()
