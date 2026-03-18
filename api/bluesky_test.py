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
