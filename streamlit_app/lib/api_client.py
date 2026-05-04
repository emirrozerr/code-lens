import json as _json
import os
import time
import urllib.parse

import requests
import streamlit as st

# Flip to False once the FastAPI backend is running
MOCK_MODE = True

BASE_URL = os.environ.get("CODELENS_API_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Mock data (module-level globals — mutated by CRUD operations in mock mode)
# ---------------------------------------------------------------------------

_MOCK_REPOS = [
    {
        "id": 1,
        "github_url": "https://github.com/acme/shop-api",
        "name": "shop-api",
        "branch": "main",
        "status": "indexed",
        "last_indexed_at": "2026-05-01T08:00:00Z",
        "function_count": 342,
        "domain_count": 7,
    },
    {
        "id": 2,
        "github_url": "https://github.com/acme/auth-service",
        "name": "auth-service",
        "branch": "main",
        "status": "indexed",
        "last_indexed_at": "2026-04-30T15:00:00Z",
        "function_count": 118,
        "domain_count": 3,
    },
]

_MOCK_DOMAINS = [
    {
        "id": 1,
        "repo_id": 1,
        "name": "Checkout",
        "member_count": 23,
        "human_verified": True,
        "summary": "Handles cart finalization, payment processing, order creation, and post-purchase email triggers.",
        "last_updated": "2026-05-01T08:01:00Z",
        "members": [
            {"symbol": "create_order", "file": "checkout/orders.py", "line": 42},
            {"symbol": "apply_discount", "file": "checkout/pricing.py", "line": 142},
            {"symbol": "validate_cart", "file": "checkout/cart.py", "line": 18},
        ],
    },
    {
        "id": 2,
        "repo_id": 1,
        "name": "Auth",
        "member_count": 14,
        "human_verified": False,
        "summary": "User authentication, session management, JWT issuance, and password hashing.",
        "last_updated": "2026-05-01T08:01:30Z",
        "members": [
            {"symbol": "login_user", "file": "auth/login.py", "line": 55},
            {"symbol": "issue_jwt", "file": "auth/tokens.py", "line": 12},
        ],
    },
    {
        "id": 3,
        "repo_id": 1,
        "name": "Payments",
        "member_count": 31,
        "human_verified": False,
        "summary": "Payment provider integration, refund logic, and transaction records.",
        "last_updated": "2026-05-01T08:02:00Z",
        "members": [
            {"symbol": "charge_card", "file": "payments/stripe.py", "line": 88},
            {"symbol": "refund_order", "file": "payments/refunds.py", "line": 34},
        ],
    },
    {
        "id": 4,
        "repo_id": 2,
        "name": "User Management",
        "member_count": 9,
        "human_verified": False,
        "summary": "User CRUD, role assignment, and profile updates.",
        "last_updated": "2026-04-30T15:01:00Z",
        "members": [
            {"symbol": "update_profile", "file": "users/profile.py", "line": 22},
        ],
    },
]

_MOCK_USERS = [
    {
        "id": 1,
        "email": "admin@example.com",
        "role": "admin",
        "created_at": "2026-01-10T09:00:00Z",
        "last_login": "2026-05-01T14:23:00Z",
        "must_change_password": False,
    },
    {
        "id": 2,
        "email": "dev@example.com",
        "role": "user",
        "created_at": "2026-02-15T10:00:00Z",
        "last_login": "2026-04-28T11:00:00Z",
        "must_change_password": True,
    },
]

_MOCK_JOBS = [
    {
        "id": 10,
        "repo_id": 1,
        "repo_name": "shop-api",
        "started_at": "2026-05-01T08:00:00Z",
        "duration_s": 47,
        "status": "success",
        "trigger": "manual",
        "error": None,
    },
    {
        "id": 9,
        "repo_id": 2,
        "repo_name": "auth-service",
        "started_at": "2026-04-30T15:00:00Z",
        "duration_s": 23,
        "status": "success",
        "trigger": "manual",
        "error": None,
    },
    {
        "id": 8,
        "repo_id": 1,
        "repo_name": "shop-api",
        "started_at": "2026-04-29T10:00:00Z",
        "duration_s": 12,
        "status": "failed",
        "trigger": "webhook",
        "error": "TreeSitter parse error on checkout/orders.py:88",
    },
    {
        "id": 7,
        "repo_id": 1,
        "repo_name": "shop-api",
        "started_at": "2026-04-28T09:00:00Z",
        "duration_s": 50,
        "status": "success",
        "trigger": "manual",
        "error": None,
    },
    {
        "id": 6,
        "repo_id": 2,
        "repo_name": "auth-service",
        "started_at": "2026-04-27T14:00:00Z",
        "duration_s": 21,
        "status": "success",
        "trigger": "manual",
        "error": None,
    },
]

_mock_next_id = {"repo": 100, "user": 100}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _headers():
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _handle_error(resp):
    if resp.status_code == 401:
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("Home.py")
    elif resp.status_code == 403:
        st.toast("Permission denied.", icon="❌")
        st.stop()
    elif resp.status_code >= 500:
        st.toast(f"Server error ({resp.status_code}). Please try again.", icon="❌")
        st.stop()


# ---------------------------------------------------------------------------
# Mock dispatch helpers
# ---------------------------------------------------------------------------

def _parse_id(path, prefix):
    """Extract integer id from path like /admin/repos/42 given prefix /admin/repos/."""
    try:
        return int(path[len(prefix):].split("?")[0].split("/")[0])
    except (ValueError, IndexError):
        return None


def _mock_get(path):
    global _MOCK_REPOS, _MOCK_DOMAINS, _MOCK_USERS, _MOCK_JOBS

    parsed = urllib.parse.urlparse(path)
    clean = parsed.path
    qs = urllib.parse.parse_qs(parsed.query)

    if clean == "/auth/me":
        return _MOCK_USERS[0]

    if clean == "/admin/repos":
        return list(_MOCK_REPOS)

    if clean.startswith("/admin/repos/"):
        rid = _parse_id(clean, "/admin/repos/")
        repo = next((r for r in _MOCK_REPOS if r["id"] == rid), None)
        if repo:
            return {
                **repo,
                "domains": [d for d in _MOCK_DOMAINS if d["repo_id"] == rid],
                "recent_jobs": [j for j in _MOCK_JOBS if j["repo_id"] == rid][:20],
            }
        return {}

    if clean.startswith("/admin/domains/"):
        did = _parse_id(clean, "/admin/domains/")
        return next((d for d in _MOCK_DOMAINS if d["id"] == did), {})

    if clean == "/admin/domains" or clean.startswith("/admin/domains"):
        repo_id_vals = qs.get("repo_id", [])
        if repo_id_vals:
            try:
                rid = int(repo_id_vals[0])
                if rid != 0:
                    return [d for d in _MOCK_DOMAINS if d["repo_id"] == rid]
            except ValueError:
                pass
        return list(_MOCK_DOMAINS)

    if clean == "/admin/users":
        return list(_MOCK_USERS)

    if clean == "/admin/jobs" or clean.startswith("/admin/jobs"):
        limit_vals = qs.get("limit", [])
        limit = int(limit_vals[0]) if limit_vals else len(_MOCK_JOBS)
        return _MOCK_JOBS[:limit]

    if clean == "/admin/dashboard/stats":
        return {
            "total_repos": len(_MOCK_REPOS),
            "total_domains": len(_MOCK_DOMAINS),
            "total_users": len(_MOCK_USERS),
            "jobs_24h": 2,
        }

    if clean == "/admin/health":
        return {
            "neo4j": "ok",
            "llm": "ok",
            "last_successful_index": "2026-05-01T08:00:00Z",
        }

    if clean == "/demo/repos":
        return list(_MOCK_REPOS)

    if clean.startswith("/demo/repos/") and clean.endswith("/domains"):
        rid = _parse_id(clean, "/demo/repos/")
        return [d for d in _MOCK_DOMAINS if d["repo_id"] == rid]

    return {}


def _mock_post(path, json_body):
    global _MOCK_REPOS, _MOCK_USERS, _mock_next_id

    parsed = urllib.parse.urlparse(path)
    clean = parsed.path
    body = json_body or {}

    if clean == "/auth/logout":
        return {}

    if clean == "/auth/change-password":
        return {"token": "mock.new.jwt.token"}

    if clean == "/admin/repos":
        url = body.get("github_url", "")
        name = url.rstrip("/").split("/")[-1] if url else "new-repo"
        new_repo = {
            "id": _mock_next_id["repo"],
            "github_url": url,
            "name": name,
            "branch": body.get("branch", "main"),
            "status": "indexed",
            "last_indexed_at": "2026-05-02T00:00:00Z",
            "function_count": 0,
            "domain_count": 0,
        }
        _mock_next_id["repo"] += 1
        _MOCK_REPOS.append(new_repo)
        return new_repo

    if clean.startswith("/admin/repos/") and clean.endswith("/reindex"):
        return {"status": "queued", "job_id": 99}

    if clean.startswith("/admin/domains/") and clean.endswith("/regenerate"):
        return {"status": "queued"}

    if clean == "/admin/users":
        new_user = {
            "id": _mock_next_id["user"],
            "email": body.get("email", "newuser@example.com"),
            "role": body.get("role", "user"),
            "created_at": "2026-05-02T00:00:00Z",
            "last_login": None,
            "must_change_password": True,
            "temporary_password": "Temp@1234",
        }
        _mock_next_id["user"] += 1
        _MOCK_USERS.append(new_user)
        return new_user

    if clean.startswith("/admin/users/") and clean.endswith("/reset-password"):
        return {"temporary_password": "Reset@5678"}

    if clean == "/demo/chat":
        # Streaming handled separately via _mock_stream
        return {}

    return {}


def _mock_patch(path, json_body):
    global _MOCK_DOMAINS, _MOCK_USERS

    parsed = urllib.parse.urlparse(path)
    clean = parsed.path
    body = json_body or {}

    if clean.startswith("/admin/domains/"):
        did = _parse_id(clean, "/admin/domains/")
        for i, d in enumerate(_MOCK_DOMAINS):
            if d["id"] == did:
                _MOCK_DOMAINS[i] = {**d, **{k: v for k, v in body.items() if v is not None}}
                return _MOCK_DOMAINS[i]
        return {}

    if clean.startswith("/admin/users/"):
        uid = _parse_id(clean, "/admin/users/")
        for i, u in enumerate(_MOCK_USERS):
            if u["id"] == uid:
                _MOCK_USERS[i] = {**u, **body}
                return _MOCK_USERS[i]
        return {}

    return {}


def _mock_delete(path):
    global _MOCK_REPOS, _MOCK_USERS

    parsed = urllib.parse.urlparse(path)
    clean = parsed.path

    if clean.startswith("/admin/repos/"):
        rid = _parse_id(clean, "/admin/repos/")
        _MOCK_REPOS[:] = [r for r in _MOCK_REPOS if r["id"] != rid]
        return {}

    if clean.startswith("/admin/users/"):
        uid = _parse_id(clean, "/admin/users/")
        _MOCK_USERS[:] = [u for u in _MOCK_USERS if u["id"] != uid]
        return {}

    return {}


_MOCK_RESPONSES = {
    "checkout": (
        "get_domain_summary", "domain_id=1",
        "Checkout domain: 23 members, human-verified.",
        [
            "The **Checkout** domain handles the full purchase lifecycle. ",
            "Key entry point is `create_order` (checkout/orders.py:42), which ",
            "validates the cart via `validate_cart`, applies discounts via ",
            "`apply_discount` (pricing.py:142), then delegates to the Payments ",
            "domain for charge processing. Post-purchase email triggers live in ",
            "`send_confirmation` (checkout/notifications.py:89).",
        ],
    ),
    "auth": (
        "get_domain_summary", "domain_id=2",
        "Auth domain: 14 members, not yet verified.",
        [
            "The **Auth** domain manages user identity and session lifecycle. ",
            "`login_user` (auth/login.py:55) validates credentials, calls ",
            "`issue_jwt` (auth/tokens.py:12) to mint a signed JWT, and stores ",
            "the session. Password hashing uses bcrypt with a work factor of 12. ",
            "Tokens expire after 24 h; refresh is not yet implemented.",
        ],
    ),
    "payment": (
        "get_domain_summary", "domain_id=3",
        "Payments domain: 31 members, not yet verified.",
        [
            "The **Payments** domain wraps Stripe. `charge_card` ",
            "(payments/stripe.py:88) is the primary entry point — it creates a ",
            "PaymentIntent, confirms it, and records the transaction. Refunds ",
            "go through `refund_order` (payments/refunds.py:34), which issues ",
            "a partial or full Stripe refund and updates the order status.",
        ],
    ),
    "discount": (
        "get_code_context", "symbol_name=apply_discount",
        "Found apply_discount in pricing.py:142 — 8 callers, 3 callees. Domain: Checkout.",
        [
            "The `apply_discount` function lives in the **Checkout** domain ",
            "(pricing.py:142). It accepts a cart total and a discount code, ",
            "validates the code against the promotions table, and applies a ",
            "percentage reduction capped at 50%. It raises `InvalidDiscountError` ",
            "if the code is expired or user-scoped but the user is not eligible.",
        ],
    ),
    "user": (
        "get_domain_summary", "domain_id=4",
        "User Management domain: 9 members, not yet verified.",
        [
            "The **User Management** domain in auth-service handles user CRUD. ",
            "`update_profile` (users/profile.py:22) accepts a partial update dict ",
            "and validates each field via Pydantic before persisting. Role ",
            "assignment is enforced server-side — the `role` field is ignored ",
            "on self-updates and requires an admin token.",
        ],
    ),
}

_MOCK_DEFAULT_RESPONSE = (
    "get_code_context", "symbol_name=<query>",
    "Context retrieved — 12 nodes, 5 edges. Domain: Checkout.",
    [
        "Based on the codebase structure, the relevant logic spans the ",
        "**Checkout** and **Payments** domains. The primary entry point is ",
        "`create_order` (checkout/orders.py:42). Business rules are enforced ",
        "at the service layer before any persistence calls are made. ",
        "Let me know if you'd like me to drill into a specific function or domain.",
    ],
)


def _mock_stream(path, json_body):
    """Yields SSE-style event dicts with realistic delays for demo feel."""
    if path != "/demo/chat":
        return

    msg = (json_body or {}).get("message", "").lower()
    key = next(
        (k for k in _MOCK_RESPONSES if k in msg),
        None,
    )
    tool_name, tool_args, result_summary, tokens = (
        _MOCK_RESPONSES[key] if key else _MOCK_DEFAULT_RESPONSE
    )

    yield {
        "event": "tool_call",
        "data": {"tool": tool_name, "args": tool_args, "status": "running"},
    }
    time.sleep(0.35)
    yield {
        "event": "tool_call",
        "data": {"tool": tool_name, "status": "done", "result_summary": result_summary},
    }
    for token in tokens:
        time.sleep(0.06)
        yield {"event": "token", "data": {"delta": token}}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_MOCK_CREDENTIALS = {
    ("user", "user"): {
        "token": "mock.jwt.user",
        "user_id": 2,
        "email": "dev@example.com",
        "role": "user",
        "must_change_password": False,
    },
    ("admin", "admin"): {
        "token": "mock.jwt.admin",
        "user_id": 1,
        "email": "admin@example.com",
        "role": "admin",
        "must_change_password": False,
    },
}


def login(email: str, password: str) -> dict:
    """Authenticate and return user dict. Raises ValueError on bad credentials."""
    if MOCK_MODE:
        result = _MOCK_CREDENTIALS.get((email.strip(), password))
        if not result:
            raise ValueError("Invalid credentials. Use user/user or admin/admin.")
        return result
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if resp.status_code == 401:
        raise ValueError("Invalid email or password.")
    _handle_error(resp)
    return resp.json()


def get(path):
    if MOCK_MODE:
        return _mock_get(path)
    resp = requests.get(f"{BASE_URL}{path}", headers=_headers())
    _handle_error(resp)
    return resp.json()


def post(path, json=None):
    if MOCK_MODE:
        return _mock_post(path, json)
    resp = requests.post(f"{BASE_URL}{path}", json=json, headers=_headers())
    _handle_error(resp)
    if resp.status_code == 204:
        return {}
    return resp.json()


def patch(path, json=None):
    if MOCK_MODE:
        return _mock_patch(path, json)
    resp = requests.patch(f"{BASE_URL}{path}", json=json, headers=_headers())
    _handle_error(resp)
    return resp.json()


def delete(path):
    if MOCK_MODE:
        return _mock_delete(path)
    resp = requests.delete(f"{BASE_URL}{path}", headers=_headers())
    _handle_error(resp)
    return {}


def stream(path, json=None):
    """Yields parsed SSE events as dicts: {"event": str, "data": dict}."""
    if MOCK_MODE:
        yield from _mock_stream(path, json)
        return

    with requests.post(
        f"{BASE_URL}{path}",
        json=json,
        headers={**_headers(), "Accept": "text/event-stream"},
        stream=True,
        timeout=(5, 120),
    ) as resp:
        _handle_error(resp)
        event_type = None
        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            if line.startswith("event:"):
                event_type = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                try:
                    data = _json.loads(data_str)
                except ValueError:
                    data = {"raw": data_str}
                yield {"event": event_type, "data": data}
                event_type = None
