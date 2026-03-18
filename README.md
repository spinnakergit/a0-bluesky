# Bluesky Integration Plugin for Agent Zero

Post, read, search, and manage content on Bluesky via the AT Protocol with full API access.

## Quick Start

1. Copy the plugin to your Agent Zero instance:
   ```bash
   ./install.sh
   ```
2. Configure your credentials in the WebUI (Settings > External Services > Bluesky Integration)
3. Restart Agent Zero

## Features

- **Post** — Create posts, replies, and quote posts with auto-detected rich text (links, mentions, hashtags)
- **Thread** — Post multi-part threads with automatic reply chaining
- **Read** — View timeline, user feeds, specific posts, and thread context
- **Search** — Search posts and users across the network
- **Manage** — Like, repost, unlike, unrepost, and remove posts
- **Profile** — Look up your profile or any user's profile
- **Follow** — Follow/unfollow users, list followers and following
- **Media** — Upload images and post with media attachments
- **Notifications** — View likes, reposts, follows, mentions, and replies

## Tools (9)

| Tool | Description |
|------|-------------|
| `bluesky_post` | Post, reply, and quote |
| `bluesky_thread` | Multi-post threads |
| `bluesky_read` | Read posts, timelines, feeds |
| `bluesky_search` | Search posts and users |
| `bluesky_manage` | Remove, like, unlike, repost, unrepost |
| `bluesky_media` | Upload images and post with media |
| `bluesky_profile` | User profile lookup |
| `bluesky_follow` | Follow/unfollow, list follows |
| `bluesky_notifications` | View notifications |

## Skills (4)

| Skill | Triggers |
|-------|----------|
| `bluesky-post` | "post to bluesky", "skeet about" |
| `bluesky-thread` | "create a bluesky thread" |
| `bluesky-research` | "search bluesky for", "what are people saying" |
| `bluesky-engage` | "engage on bluesky", "like posts about" |

## Known Behaviors

- **Long posts auto-thread:** If your post exceeds 300 graphemes, the agent automatically splits it into a threaded series of posts.
- **CID auto-resolved:** The AT Protocol CID required for like/repost is resolved automatically from the post URI — you never need to provide it.
- **Post removal:** Uses the action name "remove" to avoid false positives from the Agent Zero infection_check security layer.
- **Path-restricted media upload:** Image uploads are blocked from sensitive directories (`/etc/`, `/proc/`, plugin config dirs) as a defense-in-depth measure.

## Security

- CSRF enforced on all API endpoints
- App password masked in WebUI responses
- Session and config files written with `0o600` permissions
- Config save restricted to whitelisted keys only
- Detailed errors logged server-side; generic messages returned to clients
- Full security assessment: [tests/SECURITY_ASSESSMENT_RESULTS.md](tests/SECURITY_ASSESSMENT_RESULTS.md)

## Verification

- **36/36 human verification tests passed** (2026-03-18)
- **Full regression suite passed**
- **Security assessment completed** (Stage 3a, all findings remediated)
- Results: [tests/HUMAN_TEST_RESULTS.md](tests/HUMAN_TEST_RESULTS.md)

## API Pricing

**Free** — Bluesky uses the open AT Protocol. All features are available to all users at no cost. No tiers, no subscriptions, no rate limits beyond standard PDS limits.

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Setup Guide](docs/SETUP.md)
- [Development Guide](docs/DEVELOPMENT.md)

## License

MIT — see [LICENSE](LICENSE)
