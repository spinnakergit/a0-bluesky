# Bluesky Post Skill

Compose and publish posts on Bluesky.

## Triggers
"post to bluesky", "skeet about", "write a bluesky post"

## Steps
1. Draft the post content (max 300 graphemes)
2. If the user has provided specific text, use it directly; otherwise, compose content based on their request
3. Use the `bluesky_post` tool to publish
4. Report the result including the AT URI

## Guidelines
- Keep posts under 300 graphemes
- For longer content, suggest using bluesky_thread
- Auto-detect links, mentions (@handle.bsky.social), and hashtags
- Confirm with user before posting unless they've given explicit content
