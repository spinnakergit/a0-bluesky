# Bluesky Integration Plugin — Setup Guide

## Requirements

- Agent Zero v2026-03-13 or later
- Docker or local Python 3.10+
- Bluesky account at [bsky.app](https://bsky.app)

## Dependencies

Installed automatically by `initialize.py`:
- `aiohttp` — Async HTTP client for XRPC API calls

## Installation

### Option A: Install Script

```bash
# Copy plugin to container and run install
docker cp a0-bluesky/. a0-container:/a0/usr/plugins/bluesky/
docker exec a0-container bash /a0/usr/plugins/bluesky/install.sh
```

### Option B: Manual Installation

```bash
# Copy files
docker cp a0-bluesky/. a0-container:/a0/usr/plugins/bluesky/

# Create symlink
docker exec a0-container ln -sf /a0/usr/plugins/bluesky /a0/plugins/bluesky

# Install dependencies
docker exec a0-container /opt/venv-a0/bin/python /a0/usr/plugins/bluesky/initialize.py

# Enable the plugin
docker exec a0-container touch /a0/usr/plugins/bluesky/.toggle-1

# Restart
docker exec a0-container supervisorctl restart run_ui
```

## Bluesky Account Setup

### 1. Create an App Password

1. Go to [bsky.app/settings](https://bsky.app/settings)
2. Click **"App Passwords"** in the sidebar
3. Click **"Add App Password"**
4. Name it (e.g., "Agent Zero") and click **"Create"**
5. Copy the generated password (format: `xxxx-xxxx-xxxx-xxxx`)

> **Important:** App Passwords are separate from your account password. They can be revoked individually and provide the same access as your account.

### 2. Custom PDS (Optional)

If you run your own Personal Data Server:
- Change the PDS URL in plugin settings to your server's URL
- Your handle should be your custom domain

## Credential Mapping Reference

| What You Need | Source | Plugin Config Field |
|---|---|---|
| Handle | Your Bluesky username (e.g., `user.bsky.social`) | Settings > **Handle** |
| App Password | bsky.app > Settings > App Passwords | Settings > **App Password** |
| PDS URL | Default `https://bsky.social` (or your custom PDS) | Settings > **PDS URL** |

## Verifying Installation

1. Open Agent Zero WebUI
2. Go to Settings > External Services
3. Confirm "Bluesky Integration" appears in the plugin list
4. Click the plugin
5. Enter credentials and click "Save Bluesky Settings"
6. Click "Test Connection"
7. Expected: green "Connected as @handle" badge

## How Authentication Works

1. Plugin sends handle + app password to PDS via `com.atproto.server.createSession`
2. PDS returns `accessJwt` (short-lived, ~2hr) and `refreshJwt` (long-lived)
3. Tokens are stored in `data/session.json` (0600 permissions)
4. `accessJwt` is used for all API calls
5. When expired, plugin auto-refreshes using `refreshJwt`
6. If refresh fails, plugin re-authenticates with handle + app password

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Plugin not visible | Check `.toggle-1` exists: `ls /a0/usr/plugins/bluesky/.toggle-1` |
| Import errors | Run `initialize.py` again to install dependencies |
| "No credentials configured" | Enter handle and app password in plugin settings |
| "Login failed (401)" | Verify app password is correct — regenerate if needed |
| "Session expired" | Plugin auto-refreshes; if persistent, regenerate app password |
| Custom PDS not connecting | Verify PDS URL is reachable and includes `https://` |
