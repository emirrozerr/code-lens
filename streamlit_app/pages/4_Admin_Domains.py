from datetime import datetime, timezone

import streamlit as st

import lib.api_client as api
from lib.auth import require_admin


def _relative_time(iso: str) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        s = int(delta.total_seconds())
        if s < 60:
            return "just now"
        if s < 3600:
            m = s // 60
            return f"{m}m ago"
        if s < 86400:
            return f"{s // 3600}h ago"
        return f"{s // 86400}d ago"
    except Exception:
        return iso

require_admin()

if "selected_domain_id" not in st.session_state:
    st.session_state["selected_domain_id"] = None


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

def _render_list_view():
    st.markdown("""
    <div class="cl-page-header">
        <h1>Domains</h1>
        <p>Review and edit AI-generated domain summaries</p>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner(""):
        repos = api.get("/admin/repos")

    repo_options = {0: "All Repositories"}
    for r in repos:
        repo_options[r["id"]] = r["name"]

    selected_repo_id = st.selectbox(
        "Filter by repository",
        options=list(repo_options.keys()),
        format_func=lambda x: repo_options[x],
        label_visibility="collapsed",
    )

    query = (
        f"/admin/domains?repo_id={selected_repo_id}"
        if selected_repo_id != 0
        else "/admin/domains"
    )
    with st.spinner(""):
        domains = api.get(query)

    if not domains:
        st.info("No domains found. Index a repository to discover domains.")
        return

    st.write("")
    for domain in domains:
        with st.container(border=True):
            info_col, btn_col = st.columns([5, 1])
            with info_col:
                verified = "✅ Verified" if domain.get("human_verified") else ""
                updated = _relative_time(domain.get("last_updated", ""))
                st.markdown(
                    f"**{domain['name']}** &nbsp;"
                    f"<span style='color:#4B5563;font-size:13px'>"
                    f"{domain.get('member_count',0)} members"
                    f"{' · ' + verified if verified else ''}"
                    f"{' · Updated ' + updated if updated else ''}"
                    f"</span>",
                    unsafe_allow_html=True,
                )
                st.caption(
                    (domain.get("summary", "") or "")[:120] + ("…" if len(domain.get("summary","")) > 120 else "")
                )
            with btn_col:
                if st.button("Edit →", key=f"domain_{domain['id']}", use_container_width=True):
                    st.session_state["selected_domain_id"] = domain["id"]
                    st.rerun()


def _render_detail_view(domain_id):
    if st.button("← Back"):
        st.session_state["selected_domain_id"] = None
        st.rerun()

    with st.spinner(""):
        domain = api.get(f"/admin/domains/{domain_id}")

    if not domain:
        st.error("Domain not found.")
        return

    st.markdown(f"""
    <div class="cl-page-header">
        <h1>{domain.get('name','Domain')}</h1>
        <p>{domain.get('member_count',0)} members · {"✅ Human verified" if domain.get('human_verified') else "Not yet verified"}</p>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([3, 2], gap="large")

    with left:
        summary = st.text_area(
            "Summary",
            value=domain.get("summary", ""),
            height=160,
            help="Plain-English description of what this domain does.",
        )
        verified = st.checkbox("Mark as Human Verified", value=domain.get("human_verified", False))
        st.write("")
        save_col, regen_col = st.columns(2)
        if save_col.button("Save Changes", type="primary", use_container_width=True):
            with st.spinner("Saving…"):
                api.patch(
                    f"/admin/domains/{domain_id}",
                    json={"summary": summary, "human_verified": verified},
                )
            st.toast("Domain updated.", icon="✓")
        if regen_col.button("Re-generate with LLM", use_container_width=True):
            with st.spinner("Queuing…"):
                api.post(f"/admin/domains/{domain_id}/regenerate")
            st.toast("Regeneration queued. Ready in ~30 s.", icon="✓")

    with right:
        members = domain.get("members", [])
        st.markdown(f"#### Members ({len(members)})")
        if not members:
            st.caption("No members listed.")
        else:
            for m in members:
                st.write(f"`{m['symbol']}` — `{m['file']}:{m['line']}`")


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

if st.session_state["selected_domain_id"] is None:
    _render_list_view()
else:
    _render_detail_view(st.session_state["selected_domain_id"])
