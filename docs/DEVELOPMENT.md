# Bluesky Integration Plugin — Development Guide

## Project Structure

```
a0-bluesky/
├── plugin.yaml              # Plugin manifest
├── default_config.yaml      # Default settings
├── initialize.py            # Dependency installer (aiohttp)
├── install.sh               # Deployment script
├── .gitignore
├── helpers/
│   ├── bluesky_auth.py      # Session management, App Password auth
│   ├── bluesky_client.py    # XRPC async client with rate limiting
│   └── sanitize.py          # Post validation, facet detection, formatting
├── tools/
│   ├── bluesky_post.py      # Post, reply, quote
│   ├── bluesky_thread.py    # Multi-post threads
│   ├── bluesky_read.py      # Read posts, timelines, feeds
│   ├── bluesky_search.py    # Search posts and users
│   ├── bluesky_manage.py    # Delete, like, unlike, repost, unrepost
│   ├── bluesky_profile.py   # User profile lookup
│   ├── bluesky_follow.py    # Follow/unfollow, list follows
│   ├── bluesky_media.py     # Image upload and post
│   └── bluesky_notifications.py  # Notification feed
├── prompts/
│   ├── agent.system.tool_group.md
│   ├── agent.system.tool.bluesky_post.md
│   ├── agent.system.tool.bluesky_thread.md
│   ├── agent.system.tool.bluesky_read.md
│   ├── agent.system.tool.bluesky_search.md
│   ├── agent.system.tool.bluesky_manage.md
│   ├── agent.system.tool.bluesky_profile.md
│   ├── agent.system.tool.bluesky_follow.md
│   ├── agent.system.tool.bluesky_media.md
│   └── agent.system.tool.bluesky_notifications.md
├── skills/
│   ├── bluesky-post/SKILL.md
│   ├── bluesky-thread/SKILL.md
│   ├── bluesky-research/SKILL.md
│   └── bluesky-engage/SKILL.md
├── api/
│   ├── bluesky_config_api.py
│   └── bluesky_test.py
├── webui/
│   ├── main.html            # Dashboard (status, usage)
│   └── config.html          # Settings (handle, app password, PDS URL)
├── tests/
│   ├── regression_test.sh
│   └── HUMAN_TEST_PLAN.md
└── docs/
    ├── README.md
    ├── QUICKSTART.md
    ├── SETUP.md
    └── DEVELOPMENT.md
```

## AT Protocol Concepts

- **XRPC**: HTTP-based RPC protocol used by all AT Protocol endpoints
- **PDS**: Personal Data Server — stores user's data, handles auth
- **DID**: Decentralized Identifier — permanent user identity (`did:plc:xxx`)
- **Handle**: Human-readable username, domain-based (`user.bsky.social`)
- **AT URI**: Resource identifier (`at://did:plc:xxx/collection/rkey`)
- **CID**: Content hash — identifies exact version of a record
- **Lexicon**: Schema language defining API types and endpoints
- **Record**: Data stored in user's repository (posts, likes, follows)
- **Facets**: Rich text annotations (links, mentions, hashtags)

## Development Setup

1. Start the dev container:
   ```bash
   docker start agent-zero-dev
   ```

2. Install the plugin:
   ```bash
   docker cp a0-bluesky/. agent-zero-dev:/a0/usr/plugins/bluesky/
   docker exec agent-zero-dev ln -sf /a0/usr/plugins/bluesky /a0/plugins/bluesky
   docker exec agent-zero-dev /opt/venv-a0/bin/python /a0/usr/plugins/bluesky/initialize.py
   docker exec agent-zero-dev touch /a0/usr/plugins/bluesky/.toggle-1
   docker exec agent-zero-dev supervisorctl restart run_ui
   ```

3. Run tests:
   ```bash
   bash tests/regression_test.sh agent-zero-dev 50083
   ```

## Adding a New Tool

1. Create `tools/bluesky_<action>.py` with a Tool subclass
2. Create `prompts/agent.system.tool.bluesky_<action>.md`
3. Add API method to `helpers/bluesky_client.py` if needed
4. Add tests in `tests/regression_test.sh`
5. Update documentation

## Code Style

- Follow existing patterns from X/Discord/Signal plugins
- Use `async/await` for all I/O operations
- Always close client connections in try/finally
- Return `Response(message=..., break_loop=False)` from tools
- Use `logging.getLogger()` — never bare `print()`
- Use `self.set_progress()` for long operations
