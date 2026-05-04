import re
from datetime import datetime, timezone

import streamlit as st


def _fmt_dt(iso: str) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y  %H:%M")
    except Exception:
        return iso

import lib.api_client as api
from lib.auth import require_admin

require_admin()

_STATUS_ICONS = {"indexed": "✅", "indexing": "🔄", "failed": "❌"}

if "selected_repo_id" not in st.session_state:
    st.session_state["selected_repo_id"] = None


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

@st.dialog("Add Repository")
def _add_repo_dialog():
    with st.form("add_repo_form"):
        github_url = st.text_input("GitHub URL", placeholder="https://github.com/owner/repo")
        branch = st.text_input("Branch", value="main")
        submitted = st.form_submit_button("Add Repo", type="primary")
    if submitted:
        if not re.match(r"https://github\.com/[\w\-]+/[\w\-\.]+", github_url):
            st.error("Enter a valid GitHub URL.")
            return
        with st.spinner("Adding…"):
            api.post("/admin/repos", json={"github_url": github_url, "branch": branch})
        st.toast("Repository added.", icon="✓")
        st.rerun()


@st.dialog("Confirm Delete")
def _confirm_delete_repo_dialog():
    repo = st.session_state.get("_delete_repo_target", {})
    st.markdown(f"Delete **{repo.get('name')}**?")
    st.caption(
        f"This permanently removes **{repo.get('function_count', 0)}** functions "
        f"and **{repo.get('domain_count', 0)}** domain clusters."
    )
    st.write("")
    c1, c2 = st.columns(2)
    if c1.button("Cancel", use_container_width=True):
        st.session_state.pop("_delete_repo_target", None)
        st.rerun()
    if c2.button("Delete", type="primary", use_container_width=True):
        with st.spinner("Deleting…"):
            api.delete(f"/admin/repos/{repo['id']}")
        st.session_state.pop("_delete_repo_target", None)
        st.toast(f"'{repo['name']}' deleted.", icon="✓")
        st.rerun()


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

def _render_list_view():
    hdr, btn_col = st.columns([5, 1])
    hdr.markdown("""
    <div class="cl-page-header">
        <h1>Repositories</h1>
        <p>Manage indexed codebases</p>
    </div>
    """, unsafe_allow_html=True)
    with btn_col:
        st.write("")
        st.write("")
        if st.button("＋ Add Repo", type="primary", use_container_width=True):
            _add_repo_dialog()

    with st.spinner(""):
        repos = api.get("/admin/repos")

    if not repos:
        st.info("No repositories added yet.")
        if st.button("＋ Add your first repository", type="primary"):
            _add_repo_dialog()
        return

    for repo in repos:
        with st.container(border=True):
            top, actions = st.columns([5, 2])
            with top:
                status_icon = _STATUS_ICONS.get(repo.get("status", ""), "")
                st.markdown(
                    f"**{repo['name']}** &nbsp;`{repo['branch']}`&nbsp;&nbsp;"
                    f"{status_icon} &nbsp;"
                    f"<span style='color:#4B5563;font-size:13px'>"
                    f"{repo.get('function_count',0)} fns · "
                    f"{repo.get('domain_count',0)} domains · "
                    f"indexed {_fmt_dt(repo.get('last_indexed_at',''))}</span>",
                    unsafe_allow_html=True,
                )
            with actions:
                a1, a2, a3 = st.columns(3)
                if a1.button("View", key=f"view_{repo['id']}", use_container_width=True):
                    st.session_state["selected_repo_id"] = repo["id"]
                    st.rerun()
                if a2.button("Index", key=f"reindex_{repo['id']}", use_container_width=True):
                    with st.spinner("Queuing…"):
                        api.post(f"/admin/repos/{repo['id']}/reindex")
                    st.toast("Re-indexing started.", icon="✓")
                if a3.button("Delete", key=f"delete_{repo['id']}", use_container_width=True):
                    st.session_state["_delete_repo_target"] = repo
                    _confirm_delete_repo_dialog()


def _render_detail_view(repo_id):
    if st.button("← Back"):
        st.session_state["selected_repo_id"] = None
        st.rerun()

    with st.spinner(""):
        repo = api.get(f"/admin/repos/{repo_id}")

    if not repo:
        st.error("Repository not found.")
        return

    st.markdown(f"""
    <div class="cl-page-header">
        <h1>{repo.get('name','Repository')}</h1>
        <p>{repo.get('github_url','')}</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status",    _STATUS_ICONS.get(repo.get("status",""), repo.get("status","")))
    c2.metric("Branch",    repo.get("branch","—"))
    c3.metric("Functions", repo.get("function_count", 0))
    c4.metric("Domains",   repo.get("domain_count", 0))

    st.write("")
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("#### Domains")
        domains = repo.get("domains", [])
        if not domains:
            st.caption("No domains discovered yet.")
        else:
            for d in domains:
                verified = " ✅" if d.get("human_verified") else ""
                st.write(f"- **{d['name']}**{verified} — {d.get('member_count',0)} members")

    with right:
        st.markdown("#### Recent Jobs")
        jobs = repo.get("recent_jobs", [])
        if not jobs:
            st.caption("No jobs yet.")
        else:
            for j in jobs:
                icon = "✅" if j.get("status") == "success" else "❌"
                st.write(f"{icon} {_fmt_dt(j.get('started_at',''))} · {j.get('duration_s',0)} s")
                if j.get("error"):
                    with st.expander("Error detail"):
                        st.code(j["error"])


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

if st.session_state["selected_repo_id"] is None:
    _render_list_view()
else:
    _render_detail_view(st.session_state["selected_repo_id"])
