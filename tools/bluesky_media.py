from helpers.tool import Tool, Response


class BlueskyMedia(Tool):
    """Upload images and post with media on Bluesky."""

    async def execute(self, **kwargs) -> Response:
        image_path = self.args.get("image_path", "")
        text = self.args.get("text", "")
        alt_text = self.args.get("alt_text", "")

        if not image_path:
            return Response(message="Error: 'image_path' is required.", break_loop=False)

        import os
        # Resolve to real path and block sensitive locations
        real_path = os.path.realpath(image_path)
        _blocked = ("/etc/", "/proc/", "/sys/", "/root/", "/a0/usr/plugins/", "/a0/plugins/")
        if any(real_path.startswith(b) for b in _blocked):
            return Response(message="Error: Cannot upload files from restricted directories.", break_loop=False)

        if not os.path.isfile(real_path):
            return Response(message=f"Error: File not found: {image_path}", break_loop=False)

        file_size = os.path.getsize(real_path)
        if file_size > 1_000_000:
            return Response(message="Error: Image too large (max 1MB).", break_loop=False)

        # Determine MIME type
        ext = os.path.splitext(real_path)[1].lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(ext)
        if not mime_type:
            return Response(
                message=f"Error: Unsupported image format '{ext}'. Use PNG, JPEG, GIF, or WebP.",
                break_loop=False,
            )

        from usr.plugins.bluesky.helpers.bluesky_auth import get_bluesky_config
        config = get_bluesky_config(self.agent)
        from usr.plugins.bluesky.helpers.bluesky_client import BlueskyClient
        client = BlueskyClient(config)

        try:
            self.set_progress("Uploading image...")
            with open(real_path, "rb") as f:
                image_data = f.read()

            upload_result = await client.upload_blob(image_data, mime_type)
            if upload_result.get("error"):
                return Response(
                    message=f"Error uploading image: {upload_result.get('detail', 'Unknown error')}",
                    break_loop=False,
                )

            blob = upload_result.get("blob")
            if not blob:
                return Response(message="Error: Upload succeeded but no blob reference returned.", break_loop=False)

            if not text:
                return Response(
                    message=f"Image uploaded successfully. Blob ref: {blob}\n"
                    "Use bluesky_post with this blob to create a post with the image.",
                    break_loop=False,
                )

            # Post with the uploaded image
            from usr.plugins.bluesky.helpers.sanitize import sanitize_post_text, validate_post_length, detect_facets
            text = sanitize_post_text(text)
            ok, count = validate_post_length(text)
            if not ok:
                return Response(message=f"Post text too long: {count}/300 graphemes.", break_loop=False)

            self.set_progress("Posting with image...")
            facets = detect_facets(text)
            images = [{"image": blob, "alt": alt_text or ""}]
            result = await client.create_post(
                text=text,
                images=images,
                facets=facets if facets else None,
            )

            if result.get("error"):
                return Response(
                    message=f"Error posting: {result.get('detail', 'Unknown error')}",
                    break_loop=False,
                )

            return Response(
                message=f"Post with image created successfully.\nURI: {result.get('uri', 'unknown')}",
                break_loop=False,
            )
        finally:
            await client.close()
