# CodeLens Presentation Layer — Implementation Spec

> Combined specification for issues #11 (Admin Panel) and #12 (Demo Interface).
> Use this document as the single source of truth when building the Streamlit
> presentation layer for CodeLens.

---

## 1. Project context (what CodeLens is)

CodeLens indexes a codebase into a Neo4j knowledge graph, identifies business
domains via community detection, and exposes the graph through an MCP server so
AI agents can query structural code context. The full living spec is in
`docs/LIVING_SPEC.md`.

This document covers only the **presentation layer**:

- **Admin Panel** (#11) — admin-only management UI for repos, domains, users
- **Demo Interface** (#12) — chat UI with persona toggle for showing the system
  to stakeholders

Both run as a single Streamlit application that talks to a FastAPI backend
over HTTP. The Streamlit app does **not** access Neo4j or MCP tools directly.

---

## 2. Architecture decision

**Streamlit as a thin client calling FastAPI over HTTP.**
ADR-003 resolved with this choice. Multi-tier separation is preserved because
Streamlit (presentation) and FastAPI (application) communicate over a network
boundary, and Streamlit never accesses the data layer directly.

```
Browser
   │ HTTP
Streamlit (presentation layer) ← THIS IS WHAT WE'RE BUILDING
   │ HTTP (REST + SSE)
FastAPI (application layer) ← built by backend team
   │ Cypher / MCP
Neo4j (data layer) ← built by backend team
```

All data access in Streamlit goes through `requests.get/post/...` calls to
FastAPI endpoints. No direct DB access. No direct MCP tool calls.

---

## 3. Project structure

```
streamlit_app/
├── Home.py                       # Login page (entry point)
├── pages/
│   ├── 1_Demo.py                 # Chat UI (any authenticated user)
│   ├── 2_Admin_Dashboard.py      # Admin overview (admin only)
│   ├── 3_Admin_Repos.py          # Repo CRUD (admin only)
│   ├── 4_Admin_Domains.py        # Domain summaries (admin only)
│   └── 5_Admin_Users.py          # User management (admin only)
├── lib/
│   ├── __init__.py
│   ├── api_client.py             # Wrapper around requests for FastAPI calls
│   ├── auth.py                   # Auth helpers (require_login, require_admin)
│   └── prompts.py                # Persona system prompts (for demo agent)
└── requirements.txt              # streamlit, requests, etc.
```

Streamlit auto-discovers `pages/` and shows them in the sidebar. The number
prefix controls ordering. Underscores become spaces in the display label.

---

## 4. Authentication and session management

### 4.1 Single shared login

One login page (`Home.py`) for both admin and demo use. There is no separate
admin login. The login form posts to `POST /auth/login` and receives a JWT
containing `{ user_id, role, email, must_change_password }`.

### 4.2 Session state keys

Store these in `st.session_state` after successful login:

```python
st.session_state["token"]                    # JWT string
st.session_state["user_id"]                  # int
st.session_state["email"]                    # str
st.session_state["role"]                     # "user" | "admin"
st.session_state["must_change_password"]     # bool
```

### 4.3 Page-level guards

Every page checks auth at the top:

```python
# Any authenticated user
from lib.auth import require_login
require_login()  # redirects to Home.py if no token

# Admin-only pages
from lib.auth import require_admin
require_admin()  # shows access denied + redirects if role != "admin"
```

### 4.4 Sidebar visibility

`user` role sees only **Demo** in the sidebar. `admin` role sees Demo +
Dashboard + Repos + Domains + Users. This is achieved by hiding admin pages
when the role is not admin (Streamlit's `st.navigation` API or by setting
`PAGE_VISIBILITY` config; a simple workaround is showing a friendly "Access
Denied" message instead of the page content for non-admins).

### 4.5 First-login flow

If JWT contains `must_change_password: true`, redirect the user to a Change
Password view immediately after login. Block all other navigation until the
password is changed. Once changed, call `POST /auth/change-password`, get a
new JWT, and resume normal flow.

### 4.6 Self-registration

**Disabled.** The login page has no "Sign up" link. New users are created only
by an admin via the Users page. The first admin is created by a backend seed
script.

### 4.7 Logout

Sidebar has a Logout button. Clears `st.session_state` entirely and redirects
to `Home.py`. Optionally calls `POST /auth/logout` for backend token blacklist
(not required for MVP).

---

## 5. API client (`lib/api_client.py`)

A thin wrapper around `requests` that:

- Reads `BASE_URL` from environment (default `http://localhost:8000`)
- Attaches `Authorization: Bearer <token>` header on every call (when a token
  exists in session state)
- Handles common error cases: 401 → clear session and redirect to login;
  403 → show "permission denied" toast; 5xx → show generic error toast
- Returns parsed JSON or raises a typed exception
- Has helpers like `get(path)`, `post(path, json=...)`, `patch(...)`,
  `delete(...)`, and a streaming helper for SSE

This lets every page call e.g. `api.get("/admin/repos")` without repeating
boilerplate.

---

## 6. Admin Panel (issue #11)

### 6.1 Admin Dashboard (`pages/2_Admin_Dashboard.py`)

Sections:

1. **KPI cards** (4 metrics in columns)
   - Total repos
   - Total domains
   - Total users
   - Indexing jobs in last 24h

2. **Recent indexing jobs** (table, last 5)
   - Columns: repo, started_at, duration, status (icon), trigger
   - Failed rows expandable to show error message

3. **System health card**
   - Neo4j connection: ✓ / ✗
   - LLM API (Gemini 2.5 Flash): ✓ / rate limited / down
   - Last successful indexing: relative time

4. **Quick actions**
   - "+ Add Repo" button (opens dialog, same as on Repos page)
   - Navigation links

Data sources: `GET /admin/dashboard/stats`, `GET /admin/jobs?limit=5`,
`GET /admin/health`.

### 6.2 Repos (`pages/3_Admin_Repos.py`)

Two views in one page, switched via session state:

**List view (default)**
- Table with columns: name, branch, status (indexed/indexing/failed),
  last_indexed_at, function_count, domain_count
- Each row has actions: View Detail, Re-index Now, Delete
- Top of page: "+ Add Repo" button

**Add Repo dialog (`@st.dialog`)**
- Fields: GitHub URL (required), branch (default "main")
- Light validation: URL format check
- On submit: `POST /admin/repos` with `{ github_url, branch }`
- On success: close dialog, show toast, refresh table

**Re-index button**
- Calls `POST /admin/repos/{id}/reindex`
- Returns 202 immediately, job runs async
- Show toast: "Re-indexing started"
- Dashboard polls for status via periodic `st.rerun()` or auto-refresh

**Delete confirmation dialog (`@st.dialog`)**
- Triggered by Delete button on a row
- Shows: repo name, count of functions and domains that will be lost
- Two buttons: Cancel, Delete (Delete styled as `type="primary"` and red)
- On confirm: `DELETE /admin/repos/{id}`, toast, refresh

**Detail view** (when a repo is selected via session state)
- Shows: repo metadata, list of domains in this repo, last 20 indexing jobs
  for this repo
- "← Back to list" button at top resets selection

### 6.3 Domains (`pages/4_Admin_Domains.py`)

Two views in one page, state-based:

**List view**
- Repo filter dropdown at the top
- Table: domain name, member count, human_verified flag, last_updated
- Each row has a "View →" button that sets `selected_domain_id` and re-renders

**Detail view**
- Shows: domain name, full member list (functions + classes with file:line),
  metadata
- Editable summary in a textarea
- `human_verified` toggle (checkbox)
- Two buttons: Save Changes (`PATCH /admin/domains/{id}`),
  Re-generate with LLM (`POST /admin/domains/{id}/regenerate`)
- "← Back to list" button at top

No create or delete (domains are managed by the indexing pipeline).

### 6.4 Users (`pages/5_Admin_Users.py`)

Single list view with row-level actions.

**Table**
- Columns: email, role, created_at, last_login, must_change_password (badge)
- Per-row actions: Promote to Admin / Revoke Admin (toggles based on current
  role), Reset Password, Delete

**Add User dialog (`@st.dialog`)**
- Triggered by "+ Add User" button
- Fields: email (required), role radio (user / admin)
- On submit: `POST /admin/users` with `{ email, role }`
- Backend generates a random temporary password and returns it in the response
- A second dialog (or section in the same dialog) shows the generated password
  with a Copy button and a clear warning that this will not be shown again
- After Done: close, refresh table

**Reset Password action**
- `POST /admin/users/{id}/reset-password`
- Same flow: backend returns new temporary password, show in dialog with
  Copy button and warning

**Promote / Revoke**
- `PATCH /admin/users/{id}` with `{ role: "admin" | "user" }`
- Toast on success, refresh table

**Delete**
- Confirmation dialog (same pattern as Repos)
- `DELETE /admin/users/{id}`
- Cannot delete yourself (frontend check + backend enforcement)

---

## 7. Demo Interface (issue #12)

### 7.1 Page (`pages/1_Demo.py`)

Accessible to any authenticated user. Single chat UI with sidebar controls.

### 7.2 Sidebar controls

```
Repository: [my-shop-api ▼]      # hidden if only one repo

Persona:
( ) Developer
(•) Product Manager
( ) Legal / Compliance

[+ New Conversation]

─── Domains ───
📦 Checkout (23)
🔐 Auth (14)
💳 Payments (31)
👥 User Mgmt (9)
```

- **Repository dropdown**: lists indexed repos via `GET /demo/repos`. Hidden
  if only one repo. Changing the repo clears the conversation (different
  codebase, different context).
- **Persona radio**: stored in `st.session_state["persona"]`. Sent to backend
  on each chat request. Changing persona does NOT clear the conversation;
  the change applies to the next message.
- **New Conversation button**: clears `st.session_state.messages`.
- **Domain browser**: lists domains for the active repo via
  `GET /demo/repos/{id}/domains`. Clicking a domain auto-sends the message
  `"Tell me about the [domain name] domain."` to the chat.

### 7.3 Chat area

Use Streamlit's built-in chat components:

```python
# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Ask about the codebase..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    # ... call backend, stream response
```

### 7.4 Streaming response flow

When the user submits a message:

1. Append user message to `st.session_state.messages`.
2. Show "Thinking..." indicator (`st.spinner` or a placeholder).
3. Open SSE connection to `POST /demo/chat` with body:
   ```json
   {
     "message": "...",
     "repo_id": 123,
     "persona": "developer",
     "history": [{"role": "user", "content": "..."}, ...]
   }
   ```
4. The backend streams events. Two event types:
   - `tool_call` — `{ "tool": "get_code_context", "args": {...}, "status": "running" }`
     → render in an `st.status` widget so the user sees what the agent is doing
   - `token` — `{ "delta": "some text" }`
     → append to the assistant message and re-render with `st.write_stream`
5. When the stream ends, append the final assistant message to
   `st.session_state.messages`.

### 7.5 Tool-call transparency

Each tool call appears as a collapsible status widget in the chat:

```
🔍 Looking up apply_discount...
   ✓ Found in pricing.py:142
   ✓ Retrieved subgraph (8 callers, 3 callees)
   ✓ Domain: Checkout
```

This is valuable for demo storytelling. Show it by default; user can collapse.

### 7.6 Conversation state

- Stored in `st.session_state.messages` only.
- **Not persisted to DB.** Refresh, logout, or repo switch clears it.
- Out of scope for MVP: conversation history persistence, export to PDF/MD,
  thumbs-up/down feedback.

### 7.7 Empty states

- No repos indexed: friendly message + (admin only) "Go to Admin Panel" link.
- No domains in repo: "This repository hasn't been indexed yet."
- Empty chat (fresh conversation): example prompts like
  - "Ask about a function: 'How does apply_discount work?'"
  - "Browse domains in the sidebar"
  - "Ask about a business area: 'Tell me about Checkout'"

### 7.8 Error handling

- MCP tool failure: insert error message into chat
  (`❌ MCP tool timeout. Please try again.`)
- Gemini rate limit: insert
  (`⏳ Sending messages too quickly. Please wait ~30 seconds.`)
- Errors stay in conversation history (do not silently clear).
- Session expired (401 from backend): clear session, toast, redirect to
  `Home.py`.

---

## 8. Persona system prompts (`lib/prompts.py`)

```python
DEVELOPER_PROMPT = """
You are answering a software engineer. Include precise code references
(file:line), exact function and class names, and use technical vocabulary
freely. Be specific about types, parameters, and return values where relevant.
Cite your sources from the structural context provided by the MCP tools.
"""

PRODUCT_PROMPT = """
You are answering a product manager. Use plain English. Avoid code references,
file paths, and technical jargon. Focus on the business behavior, user-facing
implications, and edge cases. Provide example scenarios where helpful. Treat
the underlying code structure as an implementation detail the reader does not
need to see.
"""

LEGAL_PROMPT = """
You are answering a compliance officer. Frame business rules as policy clauses.
Cite the source files for traceability so any rule can be audited. Use formal,
audit-ready language. Make it explicit when a rule has exceptions or when
behavior depends on user attributes.
"""

PERSONA_PROMPTS = {
    "developer": DEVELOPER_PROMPT,
    "product": PRODUCT_PROMPT,
    "legal": LEGAL_PROMPT,
}
```

Streamlit only sends the persona key (`"developer"`, `"product"`, `"legal"`)
to the backend; the backend selects the prompt and prepends it to the agent's
system message. The prompt itself can also live on the backend — but keeping
a copy in `lib/prompts.py` is useful for documentation and demo scripts.

---

## 9. UX patterns and conventions

### 9.1 Loading
Wrap every API call in `with st.spinner("Loading..."):`. For streaming chat,
use the "Thinking..." pattern described in section 7.4.

### 9.2 Errors and feedback
- Non-critical: `st.toast("Error: ...", icon="❌")`
- Success: `st.toast("Repo deleted", icon="✓")`
- Blocking errors (session expired): full-page redirect with error message

### 9.3 Empty states
Every list view must have a friendly empty-state message with a primary CTA
(e.g., "+ Add Repo") rather than just an empty table.

### 9.4 Form validation
- Client-side: minimal (email format, required fields, URL format)
- Server-side: authoritative (Pydantic on FastAPI side)

### 9.5 Confirmation dialogs
Destructive actions (delete repo, delete user) always go through a
`@st.dialog` confirmation showing what will be lost.

### 9.6 Theme and responsiveness
- Mobile: not supported, desktop-first
- Theme: Streamlit default (auto dark/light from system)
- No custom CSS for MVP

---

## 10. Backend endpoints needed (specification for the backend team)

The Streamlit app assumes these endpoints exist on FastAPI. Build mock
implementations or stubs as needed during development; switch to real ones
once the backend team delivers them.

### Auth
- `POST /auth/login` → `{ token, user_id, email, role, must_change_password }`
- `POST /auth/logout` → 204
- `GET /auth/me` → current user info (used to refresh session)
- `POST /auth/change-password` → new JWT

### Admin: Repos
- `GET /admin/repos`
- `POST /admin/repos` → body `{ github_url, branch }`
- `GET /admin/repos/{id}` → repo detail with domains and recent jobs
- `DELETE /admin/repos/{id}`
- `POST /admin/repos/{id}/reindex` → 202

### Admin: Domains
- `GET /admin/domains?repo_id=...`
- `GET /admin/domains/{id}` → domain detail with members
- `PATCH /admin/domains/{id}` → body `{ summary?, human_verified? }`
- `POST /admin/domains/{id}/regenerate` → triggers LLM re-summary

### Admin: Users
- `GET /admin/users`
- `POST /admin/users` → body `{ email, role }` →
  response includes one-time `temporary_password`
- `PATCH /admin/users/{id}` → body `{ role }`
- `POST /admin/users/{id}/reset-password` → response includes new
  one-time `temporary_password`
- `DELETE /admin/users/{id}`

### Admin: Misc
- `GET /admin/jobs?limit=20` → recent indexing jobs across all repos
- `GET /admin/dashboard/stats` → KPI numbers
- `GET /admin/health` → Neo4j and LLM API status

### Demo
- `GET /demo/repos` → repos accessible to the current user
- `GET /demo/repos/{id}/domains` → domain list for sidebar
- `POST /demo/chat` (Server-Sent Events) → streamed agent response with
  interleaved `tool_call` and `token` events

---

## 11. LLM choice (Gemini 2.5 Flash)

The backend agent uses **Gemini 2.5 Flash** via `google-genai` (already a
dependency in `pyproject.toml`). Reasoning:

- Gemini 2.0 Flash was deprecated in March 2026 and is no longer available
  for new projects.
- Free tier on 2.5 Flash gives 10 RPM and 250 RPD — sufficient for demo and
  development.
- Same provider used for domain summaries — single LLM dependency project-wide.
- Fallback to **Gemini 2.5 Flash-Lite** (15 RPM / 1000 RPD) if rate limits
  become a problem during heavy demo usage.

The agent uses Gemini's **native function calling** — no LangGraph, no agent
SDK. The agent loop is roughly:

1. Send user message + history + tool declarations to Gemini.
2. If response is a tool call: execute the MCP tool via the MCP server,
   append the result to history, loop.
3. If response is text: stream tokens to the client.

This is implemented on the FastAPI side, not in Streamlit.

---

## 12. Out of scope (explicit deferrals)

To keep MVP tight, the following are deferred to V2:

- Conversation persistence to DB
- Conversation export (PDF / Markdown)
- User feedback (thumbs up / thumbs down)
- Email-based password reset (admin-mediated only for MVP)
- Mobile-responsive layout
- Multi-language UI (English only)
- Pagination on lists (last 20 / 50 hardcoded for MVP)
- WebSocket-based live progress (use `st.rerun()` polling instead)
- Custom theme / branding
- Audit log UI

---

## 13. Development order suggestion

If building from scratch with no backend yet, work in this order:

1. `Home.py` with login form (mock auth — accepts any email/password,
   stores fake JWT in session state with `role: "admin"`)
2. `lib/api_client.py` skeleton with mock responses
3. `pages/2_Admin_Dashboard.py` with mock data
4. `pages/3_Admin_Repos.py` with mock data and dialogs
5. `pages/5_Admin_Users.py` with mock data and dialogs
6. `pages/4_Admin_Domains.py` with mock data
7. `pages/1_Demo.py` with mock streaming (yields fake tokens)
8. Wire `lib/api_client.py` to real FastAPI endpoints once backend is ready

This order builds the frame first, then fills in functionality. Mock data
keeps the UI working in isolation while the backend is still being built.

---

## 14. Acceptance criteria

The presentation layer is "done" when:

- A user can log in via `Home.py`
- Admin sees Dashboard, Repos, Domains, Users, Demo in the sidebar; non-admin
  sees only Demo
- Admin can: add a repo, delete a repo (with confirmation), re-index a repo,
  edit a domain summary, regenerate a domain summary, add a user, reset a
  user's password, promote/revoke admin, delete a user
- Demo user can: select a repo, choose a persona, click a domain, ask
  free-text questions, see streaming responses with tool-call transparency,
  start a new conversation
- All data access goes through FastAPI (no direct Neo4j or MCP imports in
  Streamlit code)
- All destructive actions require confirmation
- Logout works and clears session
- Empty states show friendly messages
