#!/bin/bash
# Bluesky Plugin Regression Test Suite
# Runs against a live Agent Zero container with the Bluesky plugin installed.
#
# Usage:
#   ./regression_test.sh                    # Test against default (a0-verify-active on port 50088)
#   ./regression_test.sh <container> <port> # Test against specific container
#
# Requires: docker, python3 (for JSON parsing)

CONTAINER="${1:-a0-verify-active}"
PORT="${2:-50088}"
BASE_URL="http://localhost:${PORT}"

PASSED=0
FAILED=0
SKIPPED=0
ERRORS=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

pass() {
    PASSED=$((PASSED + 1))
    echo -e "  ${GREEN}PASS${NC} $1"
}

fail() {
    FAILED=$((FAILED + 1))
    ERRORS="${ERRORS}\n  - $1: $2"
    echo -e "  ${RED}FAIL${NC} $1 — $2"
}

skip() {
    SKIPPED=$((SKIPPED + 1))
    echo -e "  ${YELLOW}SKIP${NC} $1 — $2"
}

section() {
    echo ""
    echo -e "${CYAN}━━━ $1 ━━━${NC}"
}

# Helper: acquire CSRF token + session cookie from the container
CSRF_TOKEN=""
setup_csrf() {
    if [ -z "$CSRF_TOKEN" ]; then
        CSRF_TOKEN=$(docker exec "$CONTAINER" bash -c '
            curl -s -c /tmp/test_cookies.txt \
                -H "Origin: http://localhost" \
                "http://localhost/api/csrf_token" 2>/dev/null
        ' | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
    fi
}

# Helper: curl the container's internal API (with CSRF token)
api() {
    local endpoint="$1"
    local data="${2:-}"
    setup_csrf
    if [ -n "$data" ]; then
        docker exec "$CONTAINER" curl -s -X POST "http://localhost/api/plugins/bluesky/${endpoint}" \
            -H "Content-Type: application/json" \
            -H "Origin: http://localhost" \
            -H "X-CSRF-Token: ${CSRF_TOKEN}" \
            -b /tmp/test_cookies.txt \
            -d "$data" 2>/dev/null
    else
        docker exec "$CONTAINER" curl -s "http://localhost/api/plugins/bluesky/${endpoint}" \
            -H "Origin: http://localhost" \
            -H "X-CSRF-Token: ${CSRF_TOKEN}" \
            -b /tmp/test_cookies.txt 2>/dev/null
    fi
}

# Helper: run Python inside the container
pyexec() {
    docker exec "$CONTAINER" bash -c "cd /a0 && PYTHONPATH=/a0 PYTHONWARNINGS=ignore /opt/venv-a0/bin/python3 -c \"$1\"" 2>&1
}

# Helper: check file exists inside container
container_file_exists() {
    docker exec "$CONTAINER" test -f "$1" 2>/dev/null
}

# Helper: check directory exists inside container
container_dir_exists() {
    docker exec "$CONTAINER" test -d "$1" 2>/dev/null
}

echo "========================================"
echo " Bluesky Plugin Regression Test Suite"
echo "========================================"
echo "Container: $CONTAINER"
echo "Port:      $PORT"
echo "Date:      $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

########################################
section "1. Container & Service Health"
########################################

# T1.1 Container running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    pass "T1.1 Container '$CONTAINER' is running"
else
    fail "T1.1 Container '$CONTAINER' is not running" "Start it first"
    echo ""
    echo -e "${RED}FATAL: Container not running. Cannot proceed.${NC}"
    exit 1
fi

# T1.2 HTTP reachable
HTTP_STATUS=$(docker exec "$CONTAINER" curl -s -o /dev/null -w '%{http_code}' "http://localhost/" 2>/dev/null)
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "302" ]; then
    pass "T1.2 HTTP reachable (status: $HTTP_STATUS)"
else
    fail "T1.2 HTTP not reachable" "Got status: $HTTP_STATUS"
fi

# T1.3 Python venv
if docker exec "$CONTAINER" test -x /opt/venv-a0/bin/python 2>/dev/null; then
    pass "T1.3 Python venv available"
else
    fail "T1.3 Python venv not found" "/opt/venv-a0/bin/python missing"
fi

########################################
section "2. Plugin Installation"
########################################

PLUGIN_DIR="/a0/plugins/bluesky"
USR_DIR="/a0/usr/plugins/bluesky"

# T2.1 Plugin directory
if container_dir_exists "$PLUGIN_DIR" || container_dir_exists "$USR_DIR"; then
    pass "T2.1 Plugin directory exists"
else
    fail "T2.1 Plugin directory missing" "Neither $PLUGIN_DIR nor $USR_DIR"
fi

# T2.2 plugin.yaml
if container_file_exists "$PLUGIN_DIR/plugin.yaml" || container_file_exists "$USR_DIR/plugin.yaml"; then
    pass "T2.2 plugin.yaml exists"
else
    fail "T2.2 plugin.yaml missing" ""
fi

# T2.3 plugin.yaml name field
NAME_CHECK=$(pyexec "
import yaml
for p in ['$PLUGIN_DIR/plugin.yaml', '$USR_DIR/plugin.yaml']:
    try:
        d = yaml.safe_load(open(p))
        print(d.get('name', ''))
        break
    except: pass
")
if [ "$NAME_CHECK" = "bluesky" ]; then
    pass "T2.3 plugin.yaml name = 'bluesky'"
else
    fail "T2.3 plugin.yaml name field" "Expected 'bluesky', got '$NAME_CHECK'"
fi

# T2.4 Toggle file
if container_file_exists "$PLUGIN_DIR/.toggle-1" || container_file_exists "$USR_DIR/.toggle-1"; then
    pass "T2.4 .toggle-1 exists (plugin enabled)"
else
    fail "T2.4 .toggle-1 missing" "Plugin not enabled"
fi

# T2.5 Data directory
if container_dir_exists "$PLUGIN_DIR/data" || container_dir_exists "$USR_DIR/data"; then
    pass "T2.5 data/ directory exists"
else
    skip "T2.5 data/ directory" "Created on first auth"
fi

########################################
section "3. Python Imports"
########################################

# T3.1 bluesky_auth
RESULT=$(pyexec "from plugins.bluesky.helpers.bluesky_auth import get_bluesky_config, is_authenticated, has_credentials; print('ok')")
if [ "$RESULT" = "ok" ]; then
    pass "T3.1 bluesky_auth imports"
else
    fail "T3.1 bluesky_auth import" "$RESULT"
fi

# T3.2 bluesky_client
RESULT=$(pyexec "from plugins.bluesky.helpers.bluesky_client import BlueskyClient, BlueskyRateLimiter; print('ok')")
if [ "$RESULT" = "ok" ]; then
    pass "T3.2 bluesky_client imports"
else
    fail "T3.2 bluesky_client import" "$RESULT"
fi

# T3.3 sanitize
RESULT=$(pyexec "from plugins.bluesky.helpers.sanitize import sanitize_post_text, validate_post_length, detect_facets, format_post, format_profile; print('ok')")
if [ "$RESULT" = "ok" ]; then
    pass "T3.3 sanitize imports"
else
    fail "T3.3 sanitize import" "$RESULT"
fi

# T3.4 aiohttp dependency
RESULT=$(pyexec "import aiohttp; print('ok')")
if [ "$RESULT" = "ok" ]; then
    pass "T3.4 aiohttp available"
else
    fail "T3.4 aiohttp missing" "$RESULT"
fi

########################################
section "4. Auth Module Unit Tests"
########################################

# T4.1 Validate post length
RESULT=$(pyexec "
from plugins.bluesky.helpers.sanitize import validate_post_length
ok1, c1 = validate_post_length('Hello Bluesky!')
assert ok1 and c1 == 14, f'Short post: {ok1}, {c1}'
ok2, c2 = validate_post_length('x' * 301)
assert not ok2 and c2 == 301, f'Long post: {ok2}, {c2}'
ok3, c3 = validate_post_length('x' * 300)
assert ok3 and c3 == 300, f'Exact limit: {ok3}, {c3}'
print('ok')
")
if [ "$RESULT" = "ok" ]; then
    pass "T4.1 Post length validation"
else
    fail "T4.1 Post length validation" "$RESULT"
fi

# T4.2 Sanitize post text
RESULT=$(pyexec "
from plugins.bluesky.helpers.sanitize import sanitize_post_text
t1 = sanitize_post_text('  Hello\u200b World  ')
assert t1 == 'Hello World', f'Got: {repr(t1)}'
t2 = sanitize_post_text('A\n\n\n\nB')
assert t2 == 'A\n\nB', f'Got: {repr(t2)}'
print('ok')
")
if [ "$RESULT" = "ok" ]; then
    pass "T4.2 Post text sanitization"
else
    fail "T4.2 Post text sanitization" "$RESULT"
fi

# T4.3 Handle validation
RESULT=$(pyexec "
from plugins.bluesky.helpers.sanitize import validate_handle
h = validate_handle('@user.bsky.social')
assert h == 'user.bsky.social', f'Got: {h}'
h2 = validate_handle('custom.example.com')
assert h2 == 'custom.example.com', f'Got: {h2}'
try:
    validate_handle('invalid')
    assert False, 'Should have raised'
except ValueError:
    pass
print('ok')
")
if [ "$RESULT" = "ok" ]; then
    pass "T4.3 Handle validation"
else
    fail "T4.3 Handle validation" "$RESULT"
fi

# T4.4 AT URI validation
RESULT=$(pyexec "
from plugins.bluesky.helpers.sanitize import validate_at_uri
u = validate_at_uri('at://did:plc:abc123/app.bsky.feed.post/xyz')
assert u == 'at://did:plc:abc123/app.bsky.feed.post/xyz'
try:
    validate_at_uri('https://example.com')
    assert False, 'Should have raised'
except ValueError:
    pass
print('ok')
")
if [ "$RESULT" = "ok" ]; then
    pass "T4.4 AT URI validation"
else
    fail "T4.4 AT URI validation" "$RESULT"
fi

# T4.5 Facet detection (links)
RESULT=$(pyexec "
from plugins.bluesky.helpers.sanitize import detect_facets
facets = detect_facets('Check out https://example.com for more')
assert len(facets) >= 1, f'Expected at least 1 facet, got {len(facets)}'
tkey = chr(36) + 'type'
assert facets[0]['features'][0].get(tkey,'') == 'app.bsky.richtext.facet#link'
print('ok')
")
if [ "$RESULT" = "ok" ]; then
    pass "T4.5 Facet detection — links"
else
    fail "T4.5 Facet detection — links" "$RESULT"
fi

# T4.6 Facet detection (mentions)
RESULT=$(pyexec "
from plugins.bluesky.helpers.sanitize import detect_facets
facets = detect_facets('Hello @user.bsky.social!')
tkey = chr(36) + 'type'
mentions = [f for f in facets if f['features'][0].get(tkey,'') == 'app.bsky.richtext.facet#mention']
assert len(mentions) >= 1, f'Expected mention facet, got {len(mentions)}'
print('ok')
")
if [ "$RESULT" = "ok" ]; then
    pass "T4.6 Facet detection — mentions"
else
    fail "T4.6 Facet detection — mentions" "$RESULT"
fi

# T4.7 Facet detection (hashtags)
RESULT=$(pyexec "
from plugins.bluesky.helpers.sanitize import detect_facets
facets = detect_facets('Great day #AI #technology')
tkey = chr(36) + 'type'
tags = [f for f in facets if f['features'][0].get(tkey,'') == 'app.bsky.richtext.facet#tag']
assert len(tags) >= 2, f'Expected 2 tag facets, got {len(tags)}'
print('ok')
")
if [ "$RESULT" = "ok" ]; then
    pass "T4.7 Facet detection — hashtags"
else
    fail "T4.7 Facet detection — hashtags" "$RESULT"
fi

# T4.8 Format profile
RESULT=$(pyexec "
from plugins.bluesky.helpers.sanitize import format_profile
p = format_profile({'handle': 'test.bsky.social', 'displayName': 'Test', 'followersCount': 100, 'followsCount': 50, 'postsCount': 200})
assert '@test.bsky.social' in p
assert 'Test' in p
assert '100' in p
print('ok')
")
if [ "$RESULT" = "ok" ]; then
    pass "T4.8 Format profile"
else
    fail "T4.8 Format profile" "$RESULT"
fi

# T4.9 Auth module — credentials check
RESULT=$(pyexec "
from plugins.bluesky.helpers.bluesky_auth import has_credentials
assert not has_credentials({})
assert not has_credentials({'handle': 'test.bsky.social'})
assert not has_credentials({'app_password': 'xxxx'})
assert has_credentials({'handle': 'test.bsky.social', 'app_password': 'xxxx-xxxx-xxxx-xxxx'})
print('ok')
")
if [ "$RESULT" = "ok" ]; then
    pass "T4.9 Credentials check"
else
    fail "T4.9 Credentials check" "$RESULT"
fi

# T4.10 Session expired check
RESULT=$(pyexec "
import time
from plugins.bluesky.helpers.bluesky_auth import _is_session_expired
# No saved_at => expired (force re-auth)
assert _is_session_expired({})
# Recently saved => not expired
assert not _is_session_expired({'saved_at': int(time.time())})
# Old session => expired
assert _is_session_expired({'saved_at': int(time.time()) - 8000})
print('ok')
")
if [ "$RESULT" = "ok" ]; then
    pass "T4.10 Session expiry detection"
else
    fail "T4.10 Session expiry detection" "$RESULT"
fi

########################################
section "5. API Endpoints"
########################################

# T5.1 Config API responds
CONFIG_RESP=$(api "bluesky_config_api")
if echo "$CONFIG_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, dict)" 2>/dev/null; then
    pass "T5.1 Config API returns JSON"
else
    fail "T5.1 Config API" "Did not return valid JSON: $CONFIG_RESP"
fi

# T5.2 Test API responds
TEST_RESP=$(api "bluesky_test" '{}')
if echo "$TEST_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'ok' in d or 'error' in d" 2>/dev/null; then
    pass "T5.2 Test API returns ok/error"
else
    fail "T5.2 Test API" "Unexpected response: $TEST_RESP"
fi

# T5.3 CSRF enforcement
NOCSRF=$(docker exec "$CONTAINER" curl -s -X POST "http://localhost/api/plugins/bluesky/bluesky_test" \
    -H "Content-Type: application/json" \
    -d '{}' 2>/dev/null)
if echo "$NOCSRF" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('error')" 2>/dev/null; then
    pass "T5.3 CSRF enforcement (no token = error)"
else
    # A0 returns 403 HTML for CSRF failures
    if echo "$NOCSRF" | grep -qi "403\|forbidden\|csrf"; then
        pass "T5.3 CSRF enforcement (403 response)"
    else
        fail "T5.3 CSRF enforcement" "Request without CSRF token was not rejected"
    fi
fi

########################################
section "6. Tool Classes"
########################################

TOOLS=(
    "bluesky_post:BlueskyPost"
    "bluesky_thread:BlueskyThread"
    "bluesky_read:BlueskyRead"
    "bluesky_search:BlueskySearch"
    "bluesky_manage:BlueskyManage"
    "bluesky_profile:BlueskyProfile"
    "bluesky_follow:BlueskyFollow"
    "bluesky_media:BlueskyMedia"
    "bluesky_notifications:BlueskyNotifications"
)

for tool_spec in "${TOOLS[@]}"; do
    IFS=':' read -r tool_file tool_class <<< "$tool_spec"
    RESULT=$(pyexec "from plugins.bluesky.tools.${tool_file} import ${tool_class}; print('ok')" 2>/dev/null | tail -1)
    if echo "$RESULT" | grep -q "ok"; then
        pass "T6 Tool: ${tool_class}"
    else
        fail "T6 Tool: ${tool_class}" "$RESULT"
    fi
done

########################################
section "7. Prompt Files"
########################################

PROMPTS=(
    "agent.system.tool_group.md"
    "agent.system.tool.bluesky_post.md"
    "agent.system.tool.bluesky_thread.md"
    "agent.system.tool.bluesky_read.md"
    "agent.system.tool.bluesky_search.md"
    "agent.system.tool.bluesky_manage.md"
    "agent.system.tool.bluesky_profile.md"
    "agent.system.tool.bluesky_follow.md"
    "agent.system.tool.bluesky_media.md"
    "agent.system.tool.bluesky_notifications.md"
)

for prompt in "${PROMPTS[@]}"; do
    if container_file_exists "$PLUGIN_DIR/prompts/$prompt" || container_file_exists "$USR_DIR/prompts/$prompt"; then
        pass "T7 Prompt: $prompt"
    else
        fail "T7 Prompt: $prompt" "File missing"
    fi
done

########################################
section "8. Skills"
########################################

SKILLS=("bluesky-post" "bluesky-thread" "bluesky-research" "bluesky-engage")

for skill in "${SKILLS[@]}"; do
    if container_file_exists "$PLUGIN_DIR/skills/$skill/SKILL.md" || container_file_exists "$USR_DIR/skills/$skill/SKILL.md"; then
        pass "T8 Skill: $skill"
    else
        # Skills might be in usr/skills/
        if docker exec "$CONTAINER" test -f "/a0/usr/skills/$skill/SKILL.md" 2>/dev/null; then
            pass "T8 Skill: $skill (in usr/skills)"
        else
            fail "T8 Skill: $skill" "SKILL.md missing"
        fi
    fi
done

########################################
section "9. WebUI Files"
########################################

# T9.1 main.html
if container_file_exists "$PLUGIN_DIR/webui/main.html" || container_file_exists "$USR_DIR/webui/main.html"; then
    pass "T9.1 webui/main.html exists"
else
    fail "T9.1 webui/main.html" "File missing"
fi

# T9.2 config.html
if container_file_exists "$PLUGIN_DIR/webui/config.html" || container_file_exists "$USR_DIR/webui/config.html"; then
    pass "T9.2 webui/config.html exists"
else
    fail "T9.2 webui/config.html" "File missing"
fi

# T9.3 WebUI uses data attributes (not bare IDs)
RESULT=$(docker exec "$CONTAINER" bash -c "grep -c 'data-bl=' $PLUGIN_DIR/webui/main.html $USR_DIR/webui/main.html 2>/dev/null | tail -1" 2>/dev/null)
if [ -n "$RESULT" ] && [ "$RESULT" != "0" ]; then
    pass "T9.3 WebUI uses data-bl= attributes"
else
    fail "T9.3 WebUI data attributes" "Expected data-bl= attributes"
fi

# T9.4 WebUI uses fetchApi
RESULT=$(docker exec "$CONTAINER" bash -c "grep -c 'fetchApi' $PLUGIN_DIR/webui/main.html $USR_DIR/webui/main.html 2>/dev/null | tail -1" 2>/dev/null)
if [ -n "$RESULT" ] && [ "$RESULT" != "0" ]; then
    pass "T9.4 WebUI uses fetchApi"
else
    fail "T9.4 WebUI fetchApi" "Expected globalThis.fetchApi || fetch"
fi

########################################
section "10. Documentation"
########################################

DOCS=("README.md" "docs/README.md" "docs/QUICKSTART.md" "docs/DEVELOPMENT.md")

for doc in "${DOCS[@]}"; do
    if container_file_exists "$PLUGIN_DIR/$doc" || container_file_exists "$USR_DIR/$doc"; then
        pass "T10 Doc: $doc"
    else
        fail "T10 Doc: $doc" "File missing"
    fi
done

########################################
section "11. Security"
########################################

# T11.1 Config API masks sensitive fields
RESULT=$(pyexec "
import json
# Simulate config with sensitive data
from pathlib import Path
p = Path('$USR_DIR/config.json')
if not p.parent.exists():
    p = Path('$PLUGIN_DIR/config.json')
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps({'handle': 'test.bsky.social', 'app_password': 'abcd-efgh-ijkl-mnop', 'pds_url': 'https://bsky.social'}))
print('ok')
")
if [ "$RESULT" = "ok" ]; then
    MASKED=$(api "bluesky_config_api")
    if echo "$MASKED" | python3 -c "
import sys, json
d = json.load(sys.stdin)
pw = d.get('app_password', '')
assert '****' in pw, f'Password not masked: {pw}'
print('ok')
" 2>/dev/null; then
        pass "T11.1 Sensitive fields masked in GET"
    else
        fail "T11.1 Sensitive masking" "app_password not masked"
    fi
else
    skip "T11.1 Sensitive masking" "Could not write test config"
fi

# T11.2 Clean up test config
pyexec "
from pathlib import Path
for p in ['$USR_DIR/config.json', '$PLUGIN_DIR/config.json']:
    try: Path(p).unlink()
    except: pass
" > /dev/null 2>&1

########################################
# Summary
########################################

TOTAL=$((PASSED + FAILED + SKIPPED))
echo ""
echo "========================================"
echo " Results: $PASSED passed, $FAILED failed, $SKIPPED skipped (total: $TOTAL)"
echo "========================================"

if [ $FAILED -gt 0 ]; then
    echo -e "\n${RED}Failed tests:${NC}$ERRORS"
    echo ""
    exit 1
else
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
fi
