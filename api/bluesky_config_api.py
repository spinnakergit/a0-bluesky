"""API endpoint: Get/set Bluesky plugin configuration.
URL: POST /api/plugins/bluesky/bluesky_config_api
"""
import json
import yaml
from pathlib import Path
from helpers.api import ApiHandler, Request, Response


SENSITIVE_FIELDS = ["app_password"]
ALLOWED_KEYS = {"handle", "app_password", "pds_url"}


def _get_config_path() -> Path:
    """Find the writable config path."""
    candidates = [
        Path(__file__).parent.parent / "config.json",
        Path("/a0/usr/plugins/bluesky/config.json"),
        Path("/a0/plugins/bluesky/config.json"),
    ]
    for p in candidates:
        if p.parent.exists():
            return p
    return candidates[-1]


def _mask_value(val: str) -> str:
    """Mask a sensitive string value."""
    if not val or len(val) < 6:
        return "********" if val else ""
    return val[:2] + "****" + val[-2:]


class BlueskyConfigApi(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action", "get")
        if request.method == "GET" or action == "get":
            return self._get_config()
        else:
            return self._set_config(input)

    def _get_config(self) -> dict:
        try:
            config_path = _get_config_path()
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
            else:
                default_path = config_path.parent / "default_config.yaml"
                if default_path.exists():
                    with open(default_path, "r") as f:
                        config = yaml.safe_load(f) or {}
                else:
                    config = {}

            # Mask sensitive values
            masked = json.loads(json.dumps(config))
            for field in SENSITIVE_FIELDS:
                if masked.get(field):
                    masked[field] = _mask_value(masked[field])

            return masked
        except Exception:
            return {"error": "Failed to read configuration."}

    def _set_config(self, input: dict) -> dict:
        try:
            config = input.get("config", input)
            if not config or config == {"action": "set"}:
                return {"error": "No config provided"}
            config.pop("action", None)
            # Strip unknown keys (defense-in-depth)
            config = {k: v for k, v in config.items() if k in ALLOWED_KEYS}

            config_path = _get_config_path()
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Merge with existing (preserve masked sensitive fields)
            existing = {}
            if config_path.exists():
                with open(config_path, "r") as f:
                    existing = json.load(f)

            for field in SENSITIVE_FIELDS:
                new_val = config.get(field, "")
                if new_val and "****" in new_val:
                    config[field] = existing.get(field, "")

            # Atomic write with restrictive permissions (config contains app password)
            import os
            tmp = config_path.with_suffix(".tmp")
            fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                json.dump(config, f, indent=2)
            os.replace(str(tmp), str(config_path))

            return {"ok": True}
        except Exception:
            return {"error": "Failed to save configuration."}
