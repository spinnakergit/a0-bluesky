"""
Bluesky AT Protocol authentication module.

Supports:
- App Password authentication (recommended for bots/integrations)
- Session management with auto-refresh (access + refresh JWT tokens)

Authentication flow:
1. User creates an App Password at bsky.app > Settings > App Passwords
2. Plugin stores handle + app password in config
3. On first use, creates a session via com.atproto.server.createSession
4. Session tokens (accessJwt, refreshJwt) are persisted to data/session.json
5. accessJwt expires after ~2 hours; auto-refreshed using refreshJwt
"""

import os
import json
import time
import logging
from pathlib import Path

logger = logging.getLogger("bluesky_auth")

DEFAULT_PDS = "https://bsky.social"


def get_bluesky_config(agent=None):
    """Load plugin config through A0's plugin config system."""
    try:
        from helpers import plugins
        return plugins.get_plugin_config("bluesky", agent=agent) or {}
    except Exception:
        config_path = Path(__file__).parent.parent / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}


def _data_dir(config: dict) -> Path:
    """Get the data directory for storing session tokens."""
    try:
        from helpers import plugins
        plugin_dir = plugins.get_plugin_dir("bluesky")
        data_dir = Path(plugin_dir) / "data"
    except Exception:
        data_dir = Path("/a0/usr/plugins/bluesky/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _session_path(config: dict) -> Path:
    """Path to the session token file."""
    return _data_dir(config) / "session.json"


def _usage_path(config: dict) -> Path:
    """Path to the usage tracking file."""
    return _data_dir(config) / "usage.json"


def secure_write_json(path: Path, data: dict):
    """Atomic write with 0o600 permissions."""
    tmp = path.with_suffix(".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        os.unlink(str(tmp))
        raise
    os.replace(str(tmp), str(path))


def _read_json(path: Path) -> dict:
    """Read a JSON file, return empty dict if missing."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_pds_url(config: dict) -> str:
    """Get the PDS (Personal Data Server) URL."""
    return config.get("pds_url", DEFAULT_PDS).rstrip("/")


def get_handle(config: dict) -> str:
    """Get the Bluesky handle from config."""
    return config.get("handle", "").strip()


def get_app_password(config: dict) -> str:
    """Get the app password from config."""
    return config.get("app_password", "").strip()


def has_credentials(config: dict) -> bool:
    """Check if handle and app password are configured."""
    return bool(get_handle(config) and get_app_password(config))


# --- Session Management ---

def get_session(config: dict) -> dict:
    """Load stored session from file."""
    return _read_json(_session_path(config))


def save_session(config: dict, session_data: dict):
    """Persist session to file with timestamp."""
    session_data["saved_at"] = int(time.time())
    secure_write_json(_session_path(config), session_data)


def _is_session_expired(session: dict) -> bool:
    """Check if session access token is expired (assume ~2hr lifetime, 60s buffer)."""
    saved_at = session.get("saved_at", 0)
    if not saved_at:
        return True
    return time.time() > (saved_at + 7200 - 60)


def create_session(config: dict) -> dict:
    """
    Create a new session via com.atproto.server.createSession.
    Returns session dict with accessJwt, refreshJwt, did, handle.
    """
    import requests

    pds = get_pds_url(config)
    handle = get_handle(config)
    password = get_app_password(config)

    if not handle or not password:
        return {"error": "No handle or app password configured"}

    try:
        resp = requests.post(
            f"{pds}/xrpc/com.atproto.server.createSession",
            json={"identifier": handle, "password": password},
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning(f"Login failed ({resp.status_code}): {resp.text}")
            return {"error": f"Authentication failed ({resp.status_code})"}

        session = resp.json()
        save_session(config, session)
        logger.debug(f"Session created for {session.get('handle', handle)}")
        return session
    except Exception as e:
        logger.error(f"Login request failed: {e}")
        return {"error": "Authentication request failed"}


def refresh_session(config: dict) -> dict:
    """
    Refresh the session using the refreshJwt token.
    Returns new session dict or {"error": "..."}.
    """
    import requests

    session = get_session(config)
    refresh_jwt = session.get("refreshJwt", "")
    if not refresh_jwt:
        return create_session(config)

    pds = get_pds_url(config)

    try:
        resp = requests.post(
            f"{pds}/xrpc/com.atproto.server.refreshSession",
            headers={"Authorization": f"Bearer {refresh_jwt}"},
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning(f"Session refresh failed ({resp.status_code}), re-authenticating")
            return create_session(config)

        new_session = resp.json()
        save_session(config, new_session)
        logger.info("Session refreshed successfully")
        return new_session
    except Exception as e:
        logger.error(f"Refresh failed: {e}, re-authenticating")
        return create_session(config)


def get_auth_headers(config: dict) -> dict:
    """
    Get Authorization headers for XRPC requests.
    Auto-creates or refreshes session as needed.
    """
    session = get_session(config)
    access_jwt = session.get("accessJwt", "")

    if not access_jwt:
        if not has_credentials(config):
            return {}
        session = create_session(config)
        if session.get("error"):
            return {}
        access_jwt = session.get("accessJwt", "")

    elif _is_session_expired(session):
        refreshed = refresh_session(config)
        if not refreshed.get("error"):
            access_jwt = refreshed.get("accessJwt", access_jwt)

    return {"Authorization": f"Bearer {access_jwt}"}


def get_did(config: dict) -> str:
    """Get the DID (decentralized identifier) from the current session."""
    session = get_session(config)
    return session.get("did", "")


# --- Authentication Status ---

def is_authenticated(config: dict) -> tuple:
    """
    Check if credentials are valid by attempting to get profile.
    Returns (authenticated: bool, info: str).
    """
    if not has_credentials(config):
        return (False, "No credentials configured")

    try:
        import requests

        headers = get_auth_headers(config)
        if not headers:
            return (False, "Could not obtain session")

        session = get_session(config)
        did = session.get("did", "")
        if not did:
            return (False, "No DID in session")

        pds = get_pds_url(config)
        resp = requests.get(
            f"{pds}/xrpc/app.bsky.actor.getProfile",
            headers=headers,
            params={"actor": did},
            timeout=10,
        )

        if resp.status_code == 200:
            data = resp.json()
            handle = data.get("handle", "unknown")
            display = data.get("displayName", "")
            info = f"@{handle}"
            if display:
                info += f" ({display})"
            return (True, info)
        elif resp.status_code == 401:
            refreshed = refresh_session(config)
            if not refreshed.get("error"):
                retry = requests.get(
                    f"{pds}/xrpc/app.bsky.actor.getProfile",
                    headers={"Authorization": f"Bearer {refreshed['accessJwt']}"},
                    params={"actor": refreshed.get("did", did)},
                    timeout=10,
                )
                if retry.status_code == 200:
                    data = retry.json()
                    return (True, f"@{data.get('handle', 'unknown')}")
            return (False, "Session expired and refresh failed")
        else:
            return (False, f"API error ({resp.status_code})")
    except Exception as e:
        logger.error(f"Auth check failed: {e}")
        return (False, "Connection failed")


# --- Usage Tracking ---

def get_usage(config: dict) -> dict:
    """Get current month's usage stats."""
    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    usage = _read_json(_usage_path(config))
    if usage.get("month") != current_month:
        usage = {"month": current_month, "posts_created": 0, "posts_deleted": 0, "likes": 0}
        secure_write_json(_usage_path(config), usage)
    return usage


def increment_usage(config: dict, field: str = "posts_created"):
    """Increment a usage counter for the current month."""
    usage = get_usage(config)
    usage[field] = usage.get(field, 0) + 1
    secure_write_json(_usage_path(config), usage)
