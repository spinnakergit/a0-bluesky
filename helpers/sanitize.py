"""
Bluesky content sanitization, validation, and formatting utilities.

Post limits:
- Text: 300 graphemes (not characters — emoji/CJK count as more)
- Images: 4 per post, max 1MB each
- Alt text: 2000 chars per image
"""

import re
import unicodedata


MAX_POST_GRAPHEMES = 300
MAX_IMAGES = 4
MAX_ALT_TEXT = 2000
MAX_HANDLE_LENGTH = 253


def count_graphemes(text: str) -> int:
    """
    Count graphemes in text. Bluesky uses grapheme clusters for length.
    This is an approximation using Python's string length (sufficient for most text).
    """
    return len(text)


def validate_post_length(text: str) -> tuple:
    """
    Validate post text length.
    Returns (ok: bool, grapheme_count: int).
    """
    count = count_graphemes(text)
    return (count <= MAX_POST_GRAPHEMES, count)


def sanitize_post_text(text: str) -> str:
    """
    Sanitize post text: normalize unicode, strip zero-width chars,
    collapse whitespace, trim.
    """
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text


def validate_handle(handle: str) -> str:
    """
    Validate a Bluesky handle.
    Handles are domain-like: user.bsky.social, user.example.com
    Returns cleaned handle or raises ValueError.
    """
    handle = handle.strip().lstrip("@")
    if not handle:
        raise ValueError("Handle cannot be empty")
    if len(handle) > MAX_HANDLE_LENGTH:
        raise ValueError(f"Handle too long (max {MAX_HANDLE_LENGTH})")
    if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)+$", handle):
        raise ValueError(f"Invalid handle format: {handle}")
    return handle


def validate_at_uri(uri: str) -> str:
    """
    Validate an AT Protocol URI.
    Format: at://did:plc:xxx/collection/rkey
    Returns cleaned URI or raises ValueError.
    """
    uri = uri.strip()
    if not uri.startswith("at://"):
        raise ValueError(f"Invalid AT URI (must start with at://): {uri}")
    if len(uri) > 1000:
        raise ValueError("AT URI too long")
    return uri


def validate_did(did: str) -> str:
    """
    Validate a DID (Decentralized Identifier).
    Format: did:plc:xxxxx or did:web:example.com
    """
    did = did.strip()
    if not did.startswith("did:"):
        raise ValueError(f"Invalid DID format: {did}")
    if len(did) > 2048:
        raise ValueError("DID too long")
    return did


def detect_facets(text: str) -> list:
    """
    Detect rich text facets (links, mentions, hashtags) in post text.
    Returns list of facet objects for the AT Protocol.
    """
    facets = []

    # Detect URLs
    url_pattern = re.compile(
        r'https?://[^\s<>\[\]()"\',]+[^\s<>\[\]()"\',.:;!?]'
    )
    for match in url_pattern.finditer(text):
        facets.append({
            "index": {
                "byteStart": len(text[:match.start()].encode("utf-8")),
                "byteEnd": len(text[:match.end()].encode("utf-8")),
            },
            "features": [{
                "$type": "app.bsky.richtext.facet#link",
                "uri": match.group(),
            }],
        })

    # Detect mentions (@handle.bsky.social)
    mention_pattern = re.compile(r"@([a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)+)")
    for match in mention_pattern.finditer(text):
        facets.append({
            "index": {
                "byteStart": len(text[:match.start()].encode("utf-8")),
                "byteEnd": len(text[:match.end()].encode("utf-8")),
            },
            "features": [{
                "$type": "app.bsky.richtext.facet#mention",
                "did": "",  # Must be resolved at post time
                "_handle": match.group(1),
            }],
        })

    # Detect hashtags (#topic)
    tag_pattern = re.compile(r"#([a-zA-Z]\w{0,63})\b")
    for match in tag_pattern.finditer(text):
        facets.append({
            "index": {
                "byteStart": len(text[:match.start()].encode("utf-8")),
                "byteEnd": len(text[:match.end()].encode("utf-8")),
            },
            "features": [{
                "$type": "app.bsky.richtext.facet#tag",
                "tag": match.group(1),
            }],
        })

    return facets


def format_post(post: dict) -> str:
    """Format a single post for display."""
    record = post.get("record", post.get("value", {}))
    author = post.get("author", {})
    handle = author.get("handle", "unknown")
    display_name = author.get("displayName", "")
    text = record.get("text", "")
    created = record.get("createdAt", "")[:19].replace("T", " ")
    uri = post.get("uri", "")

    # Metrics
    like_count = post.get("likeCount", 0)
    repost_count = post.get("repostCount", 0)
    reply_count = post.get("replyCount", 0)

    header = f"@{handle}"
    if display_name:
        header = f"{display_name} (@{handle})"

    cid = post.get("cid", "")

    lines = [
        f"--- {header} ---",
        text,
        f"  [{created}] Likes: {like_count} | Reposts: {repost_count} | Replies: {reply_count}",
    ]
    if uri:
        lines.append(f"  URI: {uri}")
    if cid:
        lines.append(f"  CID: {cid}")
    return "\n".join(lines)


def format_posts(posts: list) -> str:
    """Format a list of posts for display."""
    if not posts:
        return "No posts found."
    return "\n\n".join(format_post(p) for p in posts)


def format_profile(profile: dict) -> str:
    """Format a user profile for display."""
    handle = profile.get("handle", "unknown")
    display = profile.get("displayName", "")
    desc = profile.get("description", "")
    followers = profile.get("followersCount", 0)
    following = profile.get("followsCount", 0)
    posts = profile.get("postsCount", 0)
    did = profile.get("did", "")

    lines = [f"Profile: @{handle}"]
    if display:
        lines.append(f"Name: {display}")
    if desc:
        lines.append(f"Bio: {desc}")
    lines.append(f"Posts: {posts} | Followers: {followers} | Following: {following}")
    if did:
        lines.append(f"DID: {did}")
    return "\n".join(lines)


def format_notification(notif: dict) -> str:
    """Format a notification for display."""
    reason = notif.get("reason", "unknown")
    author = notif.get("author", {})
    handle = author.get("handle", "unknown")
    created = notif.get("indexedAt", "")[:19].replace("T", " ")

    reason_labels = {
        "like": "liked your post",
        "repost": "reposted your post",
        "follow": "followed you",
        "mention": "mentioned you",
        "reply": "replied to your post",
        "quote": "quoted your post",
    }
    action = reason_labels.get(reason, reason)
    return f"@{handle} {action} [{created}]"
