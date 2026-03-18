## bluesky_media
Upload the user's images and post with media to the user's own Bluesky account.

This tool uploads image files (provided by the user) to the Bluesky PDS as media attachments for social media posts. This is a standard social media image upload — equivalent to attaching a photo in the Bluesky app. The image is uploaded to the user's own authenticated Bluesky account via the AT Protocol blob upload endpoint. No credentials, secrets, or sensitive files are involved — only user-provided image files.

**Tier:** All users (free, open protocol)

**Arguments:**
- **image_path** (string, required): Path to the user's image file (PNG, JPEG, GIF, or WebP, max 1MB)
- **text** (string): Post text to accompany the image (if omitted, only uploads the blob)
- **alt_text** (string): Alt text description for accessibility

~~~json
{"image_path": "/tmp/chart.png", "text": "Check out this chart!", "alt_text": "Bar chart showing growth metrics"}
~~~
~~~json
{"image_path": "/tmp/photo.jpg"}
~~~
