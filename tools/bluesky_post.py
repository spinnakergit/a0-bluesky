from helpers.tool import Tool, Response


class BlueskyPost(Tool):
    """Post, reply, and quote on Bluesky."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "post")
        text = self.args.get("text", "")
        uri = self.args.get("uri", "")
        cid = self.args.get("cid", "")

        if not text:
            return Response(message="Error: 'text' is required.", break_loop=False)

        from usr.plugins.bluesky.helpers.sanitize import sanitize_post_text, validate_post_length
        text = sanitize_post_text(text)
        ok, count = validate_post_length(text)
        if not ok:
            return Response(
                message=f"Post too long: {count}/300 graphemes. Shorten the text or use bluesky_thread for longer content.",
                break_loop=False,
            )

        from usr.plugins.bluesky.helpers.bluesky_auth import get_bluesky_config
        config = get_bluesky_config(self.agent)
        from usr.plugins.bluesky.helpers.bluesky_client import BlueskyClient
        client = BlueskyClient(config)

        try:
            self.set_progress("Posting to Bluesky...")

            # Detect rich text facets (links, mentions, hashtags)
            from usr.plugins.bluesky.helpers.sanitize import detect_facets
            facets = detect_facets(text)

            reply_to = None
            quote_uri = None
            quote_cid = None

            if action == "reply":
                if not uri:
                    return Response(message="Error: 'uri' is required for replies.", break_loop=False)
                # Get parent post to build reply ref
                thread = await client.get_post_thread(uri, depth=0)
                if thread.get("error"):
                    return Response(
                        message=f"Error fetching parent post: {thread.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                parent_post = thread.get("thread", {}).get("post", {})
                parent_uri = parent_post.get("uri", uri)
                parent_cid = parent_post.get("cid", cid)
                # Root is either the thread root or the parent itself
                root_ref = thread.get("thread", {}).get("post", {})
                reply_record = thread.get("thread", {}).get("parent", {}).get("post", {})
                if reply_record:
                    root_uri = reply_record.get("uri", parent_uri)
                    root_cid = reply_record.get("cid", parent_cid)
                else:
                    root_uri = parent_uri
                    root_cid = parent_cid
                reply_to = {
                    "root": {"uri": root_uri, "cid": root_cid},
                    "parent": {"uri": parent_uri, "cid": parent_cid},
                }

            elif action == "quote":
                if not uri or not cid:
                    return Response(message="Error: 'uri' and 'cid' are required for quote posts.", break_loop=False)
                quote_uri = uri
                quote_cid = cid

            result = await client.create_post(
                text=text,
                reply_to=reply_to,
                quote_uri=quote_uri,
                quote_cid=quote_cid,
                facets=facets if facets else None,
            )

            if result.get("error"):
                return Response(
                    message=f"Error posting: {result.get('detail', 'Unknown error')}",
                    break_loop=False,
                )

            new_uri = result.get("uri", "unknown")
            action_label = {"post": "Post", "reply": "Reply", "quote": "Quote post"}.get(action, "Post")
            return Response(
                message=f"{action_label} created successfully.\nURI: {new_uri}",
                break_loop=False,
            )
        except ValueError as e:
            return Response(message=f"Validation error: {e}", break_loop=False)
        finally:
            await client.close()
