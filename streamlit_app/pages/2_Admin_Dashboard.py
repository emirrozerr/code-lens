from datetime import datetime, timezone

import streamlit as st

import lib.api_client as api
from lib.auth import require_admin

require_admin()

import re as _re


def _fmt_dt(iso: str) -> str:
    """ISO 8601 → '01 May 2026  08:00'"""
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y  %H:%M")
    except Exception:
        return iso


def _relative_time(iso: str) -> str:
    """Return a human-readable relative time string from an ISO 8601 timestamp."""
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        s = int(delta.total_seconds())
        if s < 60:
            return "just now"
        if s < 3600:
            m = s // 60
            return f"{m} minute{'s' if m != 1 else ''} ago"
        if s < 86400:
            h = s // 3600
            return f"{h} hour{'s' if h != 1 else ''} ago"
        d = s // 86400
        return f"{d} day{'s' if d != 1 else ''} ago"
    except Exception:
        return iso

_STATUS_ICONS = {
    "success": "✅",
    "failed":  "❌",
    "running": "🔄",
    "indexed": "✅",
    "indexing":"🔄",
}


@st.dialog("Add Repository")
def _add_repo_dialog():
    with st.form("add_repo_form_dash"):
        github_url = st.text_input("GitHub URL", placeholder="https://github.com/owner/repo")
        branch = st.text_input("Branch", value="main")
        submitted = st.form_submit_button("Add Repo", type="primary")
    if submitted:
        if not _re.match(r"https://github\.com/[\w\-]+/[\w\-\.]+", github_url):
            st.error("Enter a valid GitHub URL.")
            return
        with st.spinner("Adding…"):
            api.post("/admin/repos", json={"github_url": github_url, "branch": branch})
        st.toast("Repository added.", icon="✓")
        st.rerun()


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.markdown("""
<div class="cl-page-header">
    <h1>Dashboard</h1>
    <p>System overview and recent activity</p>
</div>
""", unsafe_allow_html=True)

with st.spinner(""):
    stats  = api.get("/admin/dashboard/stats")
    jobs   = api.get("/admin/jobs?limit=5")
    health = api.get("/admin/health")

# ── KPIs ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Repositories",   stats.get("total_repos", 0))
c2.metric("Domains",        stats.get("total_domains", 0))
c3.metric("Users",          stats.get("total_users", 0))
c4.metric("Jobs (24 h)",    stats.get("jobs_24h", 0))

st.write("")

# ── Recent Jobs ────────────────────────────────────────────────────────────
left, right = st.columns([2, 1], gap="large")

with left:
    st.markdown("#### Recent Indexing Jobs")
    if not jobs:
        st.info("No indexing jobs have run yet.")
    else:
        rows = [
            {
                "Status":      _STATUS_ICONS.get(j.get("status", ""), j.get("status", "")),
                "Repository":  j.get("repo_name", "—"),
                "Started":     _fmt_dt(j.get("started_at", "")),
                "Duration":    f"{j.get('duration_s', '—')} s",
                "Trigger":     j.get("trigger", "—"),
            }
            for j in jobs
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        for j in jobs:
            if j.get("status") == "failed" and j.get("error"):
                with st.expander(f"❌  {j.get('repo_name')}  ·  {_fmt_dt(j.get('started_at', ''))}"):
                    st.code(j["error"])

# ── Health + Quick Actions ─────────────────────────────────────────────────
with right:
    st.markdown("#### System Health")
    neo4j = health.get("neo4j", "unknown")
    llm   = health.get("llm", "unknown")
    last  = health.get("last_successful_index", "—")

    with st.container(border=True):
        hc1, hc2 = st.columns(2)
        hc1.metric("Neo4j",        "✅ OK"   if neo4j == "ok" else f"❌ {neo4j}")
        hc2.metric("LLM (Gemini)", "✅ OK"   if llm   == "ok" else f"⚠️ {llm}")
        st.caption(f"Last successful index: **{_relative_time(last)}**")

    st.write("")
    st.markdown("#### Quick Actions")
    if st.button("＋ Add Repository", type="primary", use_container_width=True):
        _add_repo_dialog()
    if st.button("→ Manage Repositories", use_container_width=True):
        st.switch_page("pages/3_Admin_Repos.py")
    if st.button("→ Manage Users", use_container_width=True):
        st.switch_page("pages/5_Admin_Users.py")
