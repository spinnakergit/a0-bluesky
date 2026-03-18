# Human Test Plan: Bluesky Integration

> **Plugin:** `bluesky`
> **Version:** 1.0.0
> **Type:** Social Media (AT Protocol, App Password auth)
> **Prerequisite:** `regression_test.sh` passed 100%
> **Estimated Time:** 40-50 minutes

---

## How to Use This Plan

1. Work through each phase in order — phases are gated (Phase 2 requires Phase 1 pass, etc.)
2. For each test, perform the **Action**, check against **Expected**, tell Claude "Pass" or "Fail"
3. Claude will record results in `HUMAN_TEST_RESULTS.md` as you go
4. If any test fails: stop, troubleshoot with Claude, fix, then continue

**Start by telling Claude:** "Start human verification for bluesky"

---

## Phase 0: Prerequisites & Environment

Before starting, confirm each item:

- [ ] **Container running:** `docker ps | grep <container-name>`
- [ ] **WebUI accessible:** Open `http://localhost:<port>` in browser
- [ ] **Plugin deployed:** `docker exec <container> ls /a0/usr/plugins/bluesky/plugin.yaml`
- [ ] **Plugin enabled:** `docker exec <container> ls /a0/usr/plugins/bluesky/.toggle-1`
- [ ] **Symlink exists:** `docker exec <container> ls -la /a0/plugins/bluesky`
- [ ] **Bluesky account ready:** You have a Bluesky handle and App Password
- [ ] **Test device ready:** Bluesky app or bsky.app open for verification
- [ ] **Regression passed:** `bash regression_test.sh <container> <port>` shows 100% pass

**Record your environment:**
```
Container:     _______________
Port:          _______________
Bluesky Handle: @_______________
PDS URL:       _______________ (default: https://bsky.social)
App Password:  _______________  (first 5 chars)
```

---

## Phase 1: WebUI Verification (8 tests)

Open the Agent Zero WebUI in your browser.

| ID | Test | Action | Expected | Result |
|----|------|--------|----------|--------|
| HV-01 | Plugin in list | Navigate to Settings > External Services | "Bluesky Integration" appears in the plugin list | |
| HV-02 | Toggle | Toggle the Bluesky plugin off, then back on | Plugin disables/enables without error or page crash | |
| HV-03 | Dashboard loads | Click the Bluesky plugin dashboard tab | Dashboard renders with connection status badge showing "Checking..." then resolving | |
| HV-04 | Test connection button | Click "Test Connection" on the dashboard | Shows "Connected as @handle" when configured, with usage stats (posts, likes) | |
| HV-05 | Config loads | Click the Bluesky plugin settings tab | Config page renders with Handle, App Password, PDS URL fields, and "How to get an App Password" instructions | |
| HV-06 | No console errors | Open browser DevTools (F12) > Console tab, reload the config page | Zero JavaScript errors in console | |
| HV-07 | Password field type | Inspect the App Password input field | Input type is `password` (dots, not plaintext) | |
| HV-08 | Config saves | Enter handle, app password, and PDS URL, click Save | Success message appears (green "Saved!" or similar) | |

---

## Phase 2: Configuration & Connection (6 tests)

| ID | Test | Action | Expected | Result |
|----|------|--------|----------|--------|
| HV-09 | Config persists | Reload the config page (F5) | All fields persist — app password shows masked (e.g., "ab****op"), not empty, not plaintext | |
| HV-10 | Masked save preserves original | Click Save WITHOUT changing the masked app password field | Test Connection still works (masked value preserved, not overwritten with asterisks) | |
| HV-11 | Bad credentials error | Change app password to "invalid_password_12345", Save, then Test Connection | Shows clear error message (not a stack trace or crash) | |
| HV-12 | Restore good credentials | Re-enter correct app password, Save | Save succeeds, Test Connection works again | |
| HV-13 | Restart persistence | Run `docker exec <container> supervisorctl restart run_ui`, wait 10s, reload WebUI | Plugin still configured, Test Connection still works | |
| HV-14 | No credentials error | Remove all credentials from config, Save, try to use a tool | Agent reports "No credentials configured" or similar clear error | |

---

## Phase 3: Core Tools — bluesky_post (3 tests)

Test via the Agent Zero chat interface. Type each prompt into the agent chat.

| ID | Test | Agent Prompt | Expected | Result |
|----|------|-------------|----------|--------|
| HV-15 | Post simple message | "Post to Bluesky: Hello from Agent Zero!" | Agent uses `bluesky_post`, post appears on Bluesky, agent reports success with AT URI | |
| HV-16 | Post with facets | "Post to Bluesky: Testing #AI integration with Agent Zero https://github.com" | Hashtag and link render as clickable on Bluesky, facets correctly detected | |
| HV-17 | Post a reply | "Reply to this Bluesky post: [URI] with 'Great post!'" | Agent uses `bluesky_post` with reply parameters, reply appears threaded under original | |

---

## Phase 4: Core Tools — bluesky_thread (1 test)

| ID | Test | Agent Prompt | Expected | Result |
|----|------|-------------|----------|--------|
| HV-18 | Create thread | "Create a Bluesky thread about the benefits of AI agents. Make it 3 posts." | Agent uses `bluesky_thread`, all 3 posts appear as a connected thread, each replies to previous | |

---

## Phase 5: Core Tools — bluesky_read (3 tests)

| ID | Test | Agent Prompt | Expected | Result |
|----|------|-------------|----------|--------|
| HV-19 | Read timeline | "Show me my Bluesky timeline" | Agent uses `bluesky_read` with action "timeline", returns formatted posts with author, text, metrics | |
| HV-20 | Read user posts | "Show me posts from @bsky.app" | Agent uses `bluesky_read` with action "user_posts", returns posts from that user | |
| HV-21 | Read specific post | "Read this Bluesky post: [AT URI]" | Agent uses `bluesky_read` with action "post", returns formatted post with full details | |

---

## Phase 6: Core Tools — bluesky_search (2 tests)

| ID | Test | Agent Prompt | Expected | Result |
|----|------|-------------|----------|--------|
| HV-22 | Search posts | "Search Bluesky for posts about AI agents" | Agent uses `bluesky_search`, returns relevant posts | |
| HV-23 | Search users | "Search for Bluesky users interested in machine learning" | Agent uses `bluesky_search` with action "users", returns user profiles with follower counts | |

---

## Phase 7: Core Tools — bluesky_manage (3 tests)

| ID | Test | Agent Prompt | Expected | Result |
|----|------|-------------|----------|--------|
| HV-24 | Like a post | "Like this Bluesky post: [URI] [CID]" | Agent uses `bluesky_manage` with action "like", like appears on Bluesky | |
| HV-25 | Repost | "Repost this: [URI] [CID]" | Agent uses `bluesky_manage` with action "repost", repost appears on Bluesky | |
| HV-26 | Delete a post | Create a test post, then ask: "Delete this Bluesky post: [URI]" | Post is deleted from Bluesky | |

---

## Phase 8: Core Tools — bluesky_profile (2 tests)

| ID | Test | Agent Prompt | Expected | Result |
|----|------|-------------|----------|--------|
| HV-27 | View own profile | "Show me my Bluesky profile" | Agent uses `bluesky_profile` with action "me", returns handle, display name, bio, follower/following/post counts | |
| HV-28 | Look up another profile | "Look up @bsky.app on Bluesky" | Agent uses `bluesky_profile` with action "lookup", returns their profile info | |

---

## Phase 9: Core Tools — bluesky_follow (3 tests)

| ID | Test | Agent Prompt | Expected | Result |
|----|------|-------------|----------|--------|
| HV-29 | Follow a user | "Follow @user.bsky.social on Bluesky" | Agent uses `bluesky_follow` with action "follow", follow appears on Bluesky | |
| HV-30 | List followers | "Show my Bluesky followers" | Agent uses `bluesky_follow` with action "followers", returns list of follower handles | |
| HV-31 | List following | "Who am I following on Bluesky?" | Agent uses `bluesky_follow` with action "following", returns list of followed handles | |

---

## Phase 10: Core Tools — bluesky_media (1 test)

| ID | Test | Agent Prompt | Expected | Result |
|----|------|-------------|----------|--------|
| HV-32 | Upload and post image | "Post this image to Bluesky with text 'Check this out'" (provide image path) | Agent uses `bluesky_media`, post with image appears on Bluesky | |

---

## Phase 11: Core Tools — bluesky_notifications (1 test)

| ID | Test | Agent Prompt | Expected | Result |
|----|------|-------------|----------|--------|
| HV-33 | View notifications | "Show my Bluesky notifications" | Agent uses `bluesky_notifications`, returns likes, reposts, follows, mentions | |

---

## Phase 12: Edge Cases & Error Handling (3 tests)

| ID | Test | Action | Expected | Result |
|----|------|--------|----------|--------|
| HV-34 | Post too long | Ask agent to post text longer than 300 graphemes | Agent reports error about length limit, suggests using `bluesky_thread` | |
| HV-35 | Invalid handle | Ask: "Look up @invalid on Bluesky" | Agent reports validation error, no crash | |
| HV-36 | CSRF enforcement | Run: `curl -X POST http://localhost:<port>/api/plugins/bluesky/bluesky_test -H "Content-Type: application/json" -d '{}'` | 403 Forbidden (no CSRF token) | |

---

## Phase 13: Sign-Off

```
Plugin:           Bluesky Integration
Version:          1.0.0
Container:        _______________
Port:             _______________
Date:             _______________
Tester:           _______________

Regression Tests: ___/___ PASS
Human Tests:      ___/36  PASS  ___/36 FAIL  ___/36 SKIP
Security Assessment: Pending / Complete (see SECURITY_ASSESSMENT_RESULTS.md)

Overall:          [ ] APPROVED  [ ] NEEDS WORK  [ ] BLOCKED

Notes:
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
```

---

## Quick Troubleshooting

| Problem | Check |
|---------|-------|
| "Test Connection" fails | Is handle and app password correct? Is PDS URL reachable from the container? |
| Agent doesn't use Bluesky tools | Is plugin enabled (.toggle-1)? Restart run_ui after deploy |
| Post doesn't appear | Check Bluesky app — AT Protocol can have propagation delay |
| Facets not rendering | Check hashtag/link regex in bluesky_client.py |
| Media upload fails | Is the image path accessible inside the container? Check file size limits |
| 403 on API calls | CSRF token missing — expected behavior for unauthenticated requests |
