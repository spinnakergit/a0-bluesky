# Bluesky Integration Plugin Documentation

## Overview

Post, read, search, and manage content on Bluesky via the AT Protocol with full API access.

## Contents

- [Quick Start](QUICKSTART.md) — Installation and first-use guide
- [Setup](SETUP.md) — Detailed setup and troubleshooting
- [Development](DEVELOPMENT.md) — Contributing and development setup

## Architecture

```
a0-bluesky/
├── plugin.yaml              # Plugin manifest
├── default_config.yaml      # Default settings
├── initialize.py            # Dependency installer (aiohttp)
├── install.sh               # Deployment script
├── helpers/
│   ├── bluesky_auth.py      # Session management, App Password auth
│   ├── bluesky_client.py    # XRPC async client with rate limiting
│   └── sanitize.py          # Post validation, facet detection, formatting
├── tools/                   # 9 tools
├── prompts/                 # 10 prompt files (1 group + 9 tools)
├── skills/                  # 4 skills
├── api/                     # Config + Test endpoints
├── webui/                   # Dashboard + Settings
├── tests/                   # Regression suite + Human test plan
└── docs/                    # Documentation
```

## Tools (9)

| Tool | Description | Actions |
|------|-------------|---------|
| `bluesky_post` | Post content | post, reply, quote |
| `bluesky_thread` | Multi-post threads | — |
| `bluesky_read` | Read content | post, thread, user_posts, timeline |
| `bluesky_search` | Search | posts, users |
| `bluesky_manage` | Engagement | remove, like, unlike, repost, unrepost |
| `bluesky_profile` | Profiles | me, lookup |
| `bluesky_follow` | Social graph | follow, unfollow, followers, following |
| `bluesky_media` | Media upload | upload + post |
| `bluesky_notifications` | Notifications | list |

## Skills (4)

| Skill | Category | Triggers |
|-------|----------|----------|
| `bluesky-post` | Compose & publish | "post to bluesky", "skeet about" |
| `bluesky-thread` | Thread creation | "create a bluesky thread" |
| `bluesky-research` | Search & analyze | "search bluesky for", "what are people saying" |
| `bluesky-engage` | Engagement | "engage on bluesky", "like posts about" |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/plugins/bluesky/bluesky_config_api` | GET/POST | Config CRUD |
| `/api/plugins/bluesky/bluesky_test` | GET/POST | Connection test |

## API Pricing

**Free** — Bluesky uses the open AT Protocol. All features available to all users at no cost.
