## Bluesky Integration

Tools for posting, reading, searching, and managing content on Bluesky via the AT Protocol.

### Available Tools

**Writing**: `bluesky_post`, `bluesky_thread`, `bluesky_media`
**Reading**: `bluesky_read`, `bluesky_search`, `bluesky_notifications`
**Managing**: `bluesky_manage`, `bluesky_follow`, `bluesky_profile`

### Key Concepts

- **AT URI**: Posts are identified by AT URIs (`at://did:plc:xxx/app.bsky.feed.post/rkey`)
- **CID**: Content hash that uniquely identifies a specific version of a record
- **Handle**: Bluesky usernames are domain-based (e.g., `user.bsky.social`)
- **DID**: Decentralized Identifier — persistent user identity (`did:plc:xxx`)
- **Post limit**: 300 graphemes per post (not 280 like X/Twitter)
- **No tiers**: Bluesky API is free and open — all features available to all users

### Authentication

Uses App Password authentication (Settings > App Passwords on bsky.app).
No OAuth flow needed — just handle + app password.

### Best Practices

- Always include alt text for images (`alt_text` parameter)
- Use `bluesky_thread` for content longer than 300 graphemes
- Rich text (links, mentions, hashtags) is auto-detected
- When engaging (like/repost), you need both `uri` and `cid` of the target post
