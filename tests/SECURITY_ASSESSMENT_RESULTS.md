# Security Assessment Results: Bluesky Integration

> **Plugin:** `bluesky`
> **Version:** 1.0.0
> **Assessment Date:** 2026-03-18
> **Assessor:** Claude Code (white-box, Stage 3a)
> **Stage 3b Required:** No (2 API endpoints, no OAuth flows, no inbound webhooks)

---

## Summary

| Severity | Found | Fixed | Accepted |
|----------|-------|-------|----------|
| Critical | 1 | 1 | 0 |
| High | 0 | 0 | 0 |
| Medium | 3 | 3 | 0 |
| Low | 3 | 1 | 2 |
| Info | 4 | — | 4 |

**Overall:** All Critical and Medium findings remediated. No unresolved blocking issues.

---

## Findings

### VULN-001: Plaintext Credentials in Repository File
- **Severity:** Critical
- **File:** `tests/.bluesky_creds_backup.json`
- **Description:** Credential backup file containing real app password and handle was created during HV-14 testing. Not covered by `.gitignore`.
- **Status:** FIXED
- **Remediation:** File deleted. Added `tests/*.json` to `.gitignore`. App password should be revoked and regenerated.

### VULN-002: Config Write Without Restrictive Permissions
- **Severity:** Medium
- **File:** `api/bluesky_config_api.py:95-99`
- **Description:** `config.json` (containing app password) was written with default umask permissions (world-readable). Session files already used `0o600`.
- **Status:** FIXED
- **Remediation:** Changed to `os.open()` with `0o600` permissions + `os.replace()` atomic rename, matching the pattern in `bluesky_auth.py:secure_write_json()`.

### VULN-003: Error Responses Expose Internal Details
- **Severity:** Medium
- **Files:** `api/bluesky_test.py:44-45`, `helpers/bluesky_auth.py:146,153,273`
- **Description:** Exception class names, PDS response bodies, and network error details were returned to API callers.
- **Status:** FIXED
- **Remediation:** Replaced detailed error messages with generic ones ("Authentication failed", "Connection failed"). Details logged server-side via `logger.warning()`/`logger.error()`.

### VULN-004: No Path Traversal Protection in Media Upload
- **Severity:** Medium
- **File:** `tools/bluesky_media.py:8,16,46`
- **Description:** `image_path` from agent was used directly without path validation. Prompt injection could cause upload of sensitive files (mitigated by MIME whitelist allowing only image extensions).
- **Status:** FIXED
- **Remediation:** Added `os.path.realpath()` resolution and blocked directory list (`/etc/`, `/proc/`, `/sys/`, `/root/`, `/a0/usr/plugins/`, `/a0/plugins/`). All file operations now use resolved path.

### VULN-005: PDS URL Not Validated (SSRF Potential)
- **Severity:** Low
- **Files:** `helpers/bluesky_auth.py:86`, `helpers/bluesky_client.py:96`
- **Description:** `pds_url` config field used directly in URL construction. Could be set to internal addresses for SSRF if attacker can modify config.
- **Status:** ACCEPTED
- **Rationale:** Config modification requires CSRF token (authenticated session). Risk is low within Docker container context. Standard AT Protocol behavior expects user-configurable PDS URL for self-hosted instances.

### VULN-006: Logger Exposes Session Handle
- **Severity:** Low
- **File:** `helpers/bluesky_auth.py:150`
- **Description:** `logger.info()` logged authenticated handle on session creation.
- **Status:** FIXED
- **Remediation:** Changed to `logger.debug()` to reduce log verbosity.

### VULN-007: Config Save Allows Arbitrary Key Injection
- **Severity:** Low
- **File:** `api/bluesky_config_api.py:74-101`
- **Description:** No whitelist on config keys — any key from the POST body was written to `config.json`.
- **Status:** FIXED
- **Remediation:** Added `ALLOWED_KEYS = {"handle", "app_password", "pds_url"}` whitelist. Unknown keys are stripped before write.

---

## Positive Security Patterns

| Pattern | Status | Location |
|---------|--------|----------|
| CSRF enforcement (`requires_csrf() -> True`) | PASS | `api/bluesky_test.py:15`, `api/bluesky_config_api.py:41` |
| WebUI CSRF integration (`globalThis.fetchApi`) | PASS | `webui/main.html:23`, `webui/config.html:46` |
| WebUI data attributes (`data-bl=`) | PASS | All WebUI elements |
| Password field masking (`type="password"`) | PASS | `webui/config.html:14` |
| API response masking (sensitive fields) | PASS | `api/bluesky_config_api.py:26-30,64-68` |
| Masked value preservation on save | PASS | `api/bluesky_config_api.py:90-93` |
| Session file permissions (`0o600`) | PASS | `helpers/bluesky_auth.py:62-72` |
| Config file permissions (`0o600`) | PASS | `api/bluesky_config_api.py:97-101` (after fix) |
| Atomic file writes (tmp + rename) | PASS | `helpers/bluesky_auth.py:72`, `api/bluesky_config_api.py:97-101` |
| Input validation (handle, AT URI, DID, post length) | PASS | `helpers/sanitize.py` |
| Rate limiting with backoff | PASS | `helpers/bluesky_client.py:17-41,103-123` |
| Unicode normalization + zero-width strip | PASS | `helpers/sanitize.py:37-46` |
| No XSS vectors in WebUI | PASS | Uses `textContent`, no unescaped `innerHTML` |
| No bare `print()` in source | PASS | All logging via `logging.getLogger()` |
| CID auto-resolved (prevents hallucination) | PASS | `tools/bluesky_manage.py:43-53` |
| Path traversal protection | PASS | `tools/bluesky_media.py:16-20` (after fix) |
| Config key whitelist | PASS | `api/bluesky_config_api.py:11,80-81` (after fix) |
