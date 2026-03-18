# Bluesky Integration Plugin — Quick Start

## Prerequisites

- Agent Zero instance (Docker or local)
- Bluesky account at [bsky.app](https://bsky.app)

## Getting an App Password

1. Go to [bsky.app/settings](https://bsky.app/settings)
2. Click **"App Passwords"** in the sidebar
3. Click **"Add App Password"**
4. Name it (e.g., "Agent Zero") and click **"Create"**
5. Copy the generated password (format: `xxxx-xxxx-xxxx-xxxx`)

> **Important:** Use an App Password, NOT your account password. App Passwords can be revoked individually without affecting your account.

## Installation

```bash
# From inside the Agent Zero container:
./install.sh

# Or manually:
cp -r a0-bluesky/. /a0/usr/plugins/bluesky/
ln -sf /a0/usr/plugins/bluesky /a0/plugins/bluesky
python /a0/usr/plugins/bluesky/initialize.py
touch /a0/usr/plugins/bluesky/.toggle-1
```

## Configuration

1. Open Agent Zero WebUI
2. Go to Settings > External Services > Bluesky Integration
3. Enter your **Handle** (e.g., `user.bsky.social`)
4. Enter your **App Password** (the `xxxx-xxxx-xxxx-xxxx` you generated)
5. Leave PDS URL as default (`https://bsky.social`) unless using a custom PDS
6. Click **"Save Bluesky Settings"**
7. Click **"Test Connection"** — should show green "Connected as @handle"

### Credential Mapping

| What You Need | Where to Get It | Plugin Config Field |
|---|---|---|
| Handle | Your Bluesky username | Settings > **Handle** |
| App Password | bsky.app > Settings > App Passwords | Settings > **App Password** |
| PDS URL | Default: `https://bsky.social` | Settings > **PDS URL** |

## First Use

Ask the agent:

> "Post to Bluesky: Hello from Agent Zero!"

> "Create a Bluesky thread about the top 5 AI trends"

> "Search Bluesky for posts about crypto"

> "Show me my Bluesky timeline"

> "Look up @bsky.app on Bluesky"

## Known Behaviors

- **Long posts auto-thread:** If you ask the agent to post text exceeding 300 graphemes, it will automatically split the content into a threaded series of posts rather than just reporting an error. This is by design — the agent uses `bluesky_thread` as a fallback.
- **Post engagement (like/repost):** The CID required by the AT Protocol is resolved automatically — you only need to provide the post URI.
- **Post removal:** Uses the action name "remove" internally. The agent handles this when you say "delete" or "remove".

## Key Differences from X/Twitter

| Feature | Bluesky | X/Twitter |
|---------|---------|-----------|
| **Post limit** | 300 graphemes | 280 characters |
| **API access** | Free, open protocol | Paid tiers |
| **Auth** | App Password | OAuth 2.0 + PKCE |
| **Post ID** | AT URI (`at://did:plc:.../...`) | Numeric tweet ID |
| **User ID** | DID (`did:plc:...`) | Numeric user ID |
| **Handle** | Domain-based (`user.bsky.social`) | `@username` |
