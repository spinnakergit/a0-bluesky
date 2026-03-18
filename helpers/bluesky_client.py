"""
Bluesky AT Protocol XRPC client with rate limiting and retry logic.

All Bluesky API calls go through XRPC (Cross-RPC) endpoints on the user's PDS.
Public read endpoints can also hit the AppView at https://public.api.bsky.app.
"""

import asyncio
import time
import json
import logging
import aiohttp

logger = logging.getLogger("bluesky_client")


class BlueskyRateLimiter:
    """Track rate limits from XRPC response headers."""

    def __init__(self):
        self._limits = {}
        self._lock = asyncio.Lock()

    async def wait(self, endpoint: str):
        """Block if endpoint is currently rate-limited."""
        async with self._lock:
            info = self._limits.get(endpoint)
            if info and info["remaining"] <= 0:
                wait_time = info["reset_at"] - time.time()
                if wait_time > 0:
                    await asyncio.sleep(min(wait_time, 60))

    def update(self, endpoint: str, headers: dict):
        """Update rate limit state from response headers."""
        remaining = headers.get("ratelimit-remaining")
        reset = headers.get("ratelimit-reset")
        if remaining is not None and reset is not None:
            self._limits[endpoint] = {
                "remaining": int(remaining),
                "reset_at": int(reset),
            }


class BlueskyClient:
    """Async Bluesky AT Protocol XRPC client."""

    def __init__(self, config: dict):
        self.config = config
        self._session = None
        self._rate_limiter = BlueskyRateLimiter()

    @classmethod
    def from_config(cls, agent=None):
        """Factory: create client from A0 plugin config."""
        from plugins.bluesky.helpers.bluesky_auth import get_bluesky_config
        config = get_bluesky_config(agent)
        return cls(config)

    def _get_pds(self) -> str:
        from plugins.bluesky.helpers.bluesky_auth import get_pds_url
        return get_pds_url(self.config)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_headers(self) -> dict:
        """Get auth headers for XRPC requests."""
        from plugins.bluesky.helpers.bluesky_auth import get_auth_headers
        headers = get_auth_headers(self.config)
        headers["Content-Type"] = "application/json"
        return headers

    def _get_did(self) -> str:
        """Get the DID from session."""
        from plugins.bluesky.helpers.bluesky_auth import get_did
        return get_did(self.config)

    async def _request(
        self,
        method: str,
        nsid: str,
        json_body: dict = None,
        params: dict = None,
        data: bytes = None,
        content_type: str = None,
        max_retries: int = 3,
    ) -> dict:
        """Core XRPC request method with rate limiting and retry."""
        pds = self._get_pds()
        url = f"{pds}/xrpc/{nsid}"
        headers = self._get_headers()
        if content_type:
            headers["Content-Type"] = content_type

        session = await self._get_session()

        for attempt in range(max_retries):
            await self._rate_limiter.wait(nsid)

            try:
                kwargs = {"headers": headers}
                if json_body is not None:
                    kwargs["json"] = json_body
                if params:
                    kwargs["params"] = params
                if data is not None:
                    kwargs["data"] = data

                async with session.request(method, url, **kwargs) as resp:
                    self._rate_limiter.update(nsid, dict(resp.headers))

                    if resp.status == 429:
                        retry_after = resp.headers.get("retry-after", "5")
                        wait = min(int(retry_after), 60) * (attempt + 1)
                        logger.warning(f"Rate limited on {nsid}, waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue

                    body = await resp.text()
                    if resp.status >= 400:
                        return {
                            "error": True,
                            "status": resp.status,
                            "detail": body,
                        }

                    if body:
                        return json.loads(body)
                    return {"ok": True}
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    return {"error": True, "detail": str(e)}
                await asyncio.sleep(2 ** attempt)

        return {"error": True, "detail": "Max retries exceeded"}

    # --- Post Operations ---

    async def create_post(
        self,
        text: str,
        reply_to: dict = None,
        quote_uri: str = None,
        quote_cid: str = None,
        images: list = None,
        facets: list = None,
        langs: list = None,
    ) -> dict:
        """
        Create a post (skeet).

        Args:
            text: Post text (max 300 graphemes)
            reply_to: {"root": {"uri": ..., "cid": ...}, "parent": {"uri": ..., "cid": ...}}
            quote_uri: URI of post to quote
            quote_cid: CID of post to quote
            images: List of {"blob": blob_ref, "alt": alt_text} dicts
            facets: Rich text facets (links, mentions, tags)
            langs: Language codes e.g. ["en"]
        """
        from datetime import datetime, timezone
        did = self._get_did()
        if not did:
            return {"error": True, "detail": "No authenticated session (no DID)"}

        record = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        if reply_to:
            record["reply"] = reply_to
        if quote_uri and quote_cid:
            record["embed"] = {
                "$type": "app.bsky.embed.record",
                "record": {"uri": quote_uri, "cid": quote_cid},
            }
        if images:
            record["embed"] = {
                "$type": "app.bsky.embed.images",
                "images": images,
            }
        if facets:
            record["facets"] = facets
        if langs:
            record["langs"] = langs

        result = await self._request(
            "POST",
            "com.atproto.repo.createRecord",
            json_body={
                "repo": did,
                "collection": "app.bsky.feed.post",
                "record": record,
            },
        )

        if not result.get("error"):
            from plugins.bluesky.helpers.bluesky_auth import increment_usage
            increment_usage(self.config)

        return result

    async def delete_post(self, uri: str) -> dict:
        """Delete a post by AT URI."""
        did = self._get_did()
        rkey = uri.split("/")[-1] if "/" in uri else uri
        result = await self._request(
            "POST",
            "com.atproto.repo.deleteRecord",
            json_body={
                "repo": did,
                "collection": "app.bsky.feed.post",
                "rkey": rkey,
            },
        )
        if not result.get("error"):
            from plugins.bluesky.helpers.bluesky_auth import increment_usage
            increment_usage(self.config, "posts_deleted")
        return result

    async def get_post_thread(self, uri: str, depth: int = 6) -> dict:
        """Get a post and its thread context."""
        return await self._request(
            "GET",
            "app.bsky.feed.getPostThread",
            params={"uri": uri, "depth": depth},
        )

    async def get_posts(self, uris: list) -> dict:
        """Get multiple posts by URI."""
        return await self._request(
            "GET",
            "app.bsky.feed.getPosts",
            params={"uris": uris},
        )

    # --- Feed Operations ---

    async def get_timeline(self, limit: int = 30, cursor: str = None) -> dict:
        """Get the authenticated user's home timeline."""
        params = {"limit": min(limit, 100)}
        if cursor:
            params["cursor"] = cursor
        return await self._request("GET", "app.bsky.feed.getTimeline", params=params)

    async def get_author_feed(self, actor: str, limit: int = 30, cursor: str = None) -> dict:
        """Get posts from a specific user."""
        params = {"actor": actor, "limit": min(limit, 100)}
        if cursor:
            params["cursor"] = cursor
        return await self._request("GET", "app.bsky.feed.getAuthorFeed", params=params)

    # --- Search ---

    async def search_posts(self, query: str, limit: int = 25, sort: str = "latest", cursor: str = None) -> dict:
        """Search posts."""
        params = {"q": query, "limit": min(limit, 100), "sort": sort}
        if cursor:
            params["cursor"] = cursor
        return await self._request("GET", "app.bsky.feed.searchPosts", params=params)

    async def search_actors(self, query: str, limit: int = 25) -> dict:
        """Search for users/actors."""
        params = {"q": query, "limit": min(limit, 25)}
        return await self._request("GET", "app.bsky.actor.searchActors", params=params)

    # --- Profile ---

    async def get_profile(self, actor: str = None) -> dict:
        """Get a user profile. Defaults to authenticated user."""
        if not actor:
            actor = self._get_did()
        return await self._request(
            "GET",
            "app.bsky.actor.getProfile",
            params={"actor": actor},
        )

    # --- Engagement ---

    async def like_post(self, uri: str, cid: str) -> dict:
        """Like a post."""
        from datetime import datetime, timezone
        did = self._get_did()
        result = await self._request(
            "POST",
            "com.atproto.repo.createRecord",
            json_body={
                "repo": did,
                "collection": "app.bsky.feed.like",
                "record": {
                    "$type": "app.bsky.feed.like",
                    "subject": {"uri": uri, "cid": cid},
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                },
            },
        )
        if not result.get("error"):
            from plugins.bluesky.helpers.bluesky_auth import increment_usage
            increment_usage(self.config, "likes")
        return result

    async def unlike_post(self, like_uri: str) -> dict:
        """Unlike a post by deleting the like record."""
        did = self._get_did()
        rkey = like_uri.split("/")[-1] if "/" in like_uri else like_uri
        return await self._request(
            "POST",
            "com.atproto.repo.deleteRecord",
            json_body={
                "repo": did,
                "collection": "app.bsky.feed.like",
                "rkey": rkey,
            },
        )

    async def repost(self, uri: str, cid: str) -> dict:
        """Repost (retweet equivalent)."""
        from datetime import datetime, timezone
        did = self._get_did()
        return await self._request(
            "POST",
            "com.atproto.repo.createRecord",
            json_body={
                "repo": did,
                "collection": "app.bsky.feed.repost",
                "record": {
                    "$type": "app.bsky.feed.repost",
                    "subject": {"uri": uri, "cid": cid},
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                },
            },
        )

    async def unrepost(self, repost_uri: str) -> dict:
        """Remove a repost."""
        did = self._get_did()
        rkey = repost_uri.split("/")[-1] if "/" in repost_uri else repost_uri
        return await self._request(
            "POST",
            "com.atproto.repo.deleteRecord",
            json_body={
                "repo": did,
                "collection": "app.bsky.feed.repost",
                "rkey": rkey,
            },
        )

    # --- Social Graph ---

    async def follow(self, did: str) -> dict:
        """Follow a user."""
        from datetime import datetime, timezone
        my_did = self._get_did()
        return await self._request(
            "POST",
            "com.atproto.repo.createRecord",
            json_body={
                "repo": my_did,
                "collection": "app.bsky.graph.follow",
                "record": {
                    "$type": "app.bsky.graph.follow",
                    "subject": did,
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                },
            },
        )

    async def unfollow(self, follow_uri: str) -> dict:
        """Unfollow a user by deleting the follow record."""
        my_did = self._get_did()
        rkey = follow_uri.split("/")[-1] if "/" in follow_uri else follow_uri
        return await self._request(
            "POST",
            "com.atproto.repo.deleteRecord",
            json_body={
                "repo": my_did,
                "collection": "app.bsky.graph.follow",
                "rkey": rkey,
            },
        )

    async def get_follows(self, actor: str = None, limit: int = 50) -> dict:
        """Get who a user follows."""
        if not actor:
            actor = self._get_did()
        return await self._request(
            "GET",
            "app.bsky.graph.getFollows",
            params={"actor": actor, "limit": min(limit, 100)},
        )

    async def get_followers(self, actor: str = None, limit: int = 50) -> dict:
        """Get a user's followers."""
        if not actor:
            actor = self._get_did()
        return await self._request(
            "GET",
            "app.bsky.graph.getFollowers",
            params={"actor": actor, "limit": min(limit, 100)},
        )

    # --- Media ---

    async def upload_blob(self, image_data: bytes, mime_type: str = "image/png") -> dict:
        """Upload an image blob to the PDS."""
        return await self._request(
            "POST",
            "com.atproto.repo.uploadBlob",
            data=image_data,
            content_type=mime_type,
        )

    # --- Notifications ---

    async def get_notifications(self, limit: int = 30) -> dict:
        """Get notifications (likes, reposts, follows, mentions, replies)."""
        return await self._request(
            "GET",
            "app.bsky.notification.listNotifications",
            params={"limit": min(limit, 100)},
        )
