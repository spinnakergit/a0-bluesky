"""API endpoint: Test Bluesky connection.
URL: POST /api/plugins/bluesky/bluesky_test
"""
from helpers.api import ApiHandler, Request, Response


class BlueskyTest(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            # Self-heal: ensure symlink exists for plugin namespace imports
            from pathlib import Path
            plugin_dir = Path(__file__).resolve().parent.parent
            for root in [Path("/a0"), Path("/git/agent-zero")]:
                plugins_dir = root / "plugins"
                if plugins_dir.is_dir():
                    symlink = plugins_dir / "bluesky"
                    if not symlink.exists():
                        symlink.symlink_to(plugin_dir)
                    break

            from plugins.bluesky.helpers.bluesky_auth import (
                get_bluesky_config,
                is_authenticated,
                has_credentials,
                get_usage,
            )

            config = get_bluesky_config()
            if not has_credentials(config):
                return {"ok": False, "error": "No credentials configured. Set handle and app password."}

            authenticated, info = is_authenticated(config)
            if authenticated:
                usage = get_usage(config)
                return {
                    "ok": True,
                    "user": info,
                    "usage": {
                        "month": usage.get("month", ""),
                        "posts_created": usage.get("posts_created", 0),
                        "likes": usage.get("likes", 0),
                    },
                }
            else:
                return {"ok": False, "error": info}
        except Exception:
            return {"ok": False, "error": "Connection failed. Check credentials and PDS URL."}
