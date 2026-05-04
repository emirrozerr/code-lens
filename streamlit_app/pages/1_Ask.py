import streamlit as st

import lib.api_client as api
from lib.auth import require_login
from lib.prompts import PERSONA_LABELS

require_login()

# ---------------------------------------------------------------------------
# Session init
# ---------------------------------------------------------------------------
if "messages"         not in st.session_state: st.session_state["messages"]         = []
if "persona"          not in st.session_state: st.session_state["persona"]           = "developer"
if "selected_repo_id" not in st.session_state: st.session_state["selected_repo_id"] = None
if "_last_repo_id"    not in st.session_state: st.session_state["_last_repo_id"]     = None

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    with st.spinner(""):
        repos = api.get("/demo/repos")

    if not repos:
        st.warning("No repositories indexed.")
        if st.session_state.get("role") == "admin":
            if st.button("Go to Admin Panel", use_container_width=True):
                st.switch_page("pages/2_Admin_Dashboard.py")
        st.stop()

    st.markdown("---")

    # ── Repo selector ─────────────────────────────────────────
    if len(repos) > 1:
        repo_map = {r["id"]: r["name"] for r in repos}
        new_repo_id = st.selectbox(
            "Repository",
            options=list(repo_map.keys()),
            format_func=lambda x: repo_map[x],
        )
    else:
        new_repo_id = repos[0]["id"]
        st.markdown(f"**Repository:** {repos[0]['name']}")

    if st.session_state["_last_repo_id"] is not None and new_repo_id != st.session_state["_last_repo_id"]:
        st.session_state["messages"] = []
    st.session_state["selected_repo_id"] = new_repo_id
    st.session_state["_last_repo_id"]    = new_repo_id

    # ── Persona ───────────────────────────────────────────────
    st.write("")
    st.caption("Persona")
    _PERSONA_SHORT = {"developer": "Dev", "product": "PM", "legal": "Legal"}
    p1, p2, p3 = st.columns(3)
    for col, (key, short) in zip([p1, p2, p3], _PERSONA_SHORT.items()):
        active = st.session_state["persona"] == key
        if col.button(short, key=f"p_{key}", type="primary" if active else "secondary", use_container_width=True):
            st.session_state["persona"] = key
            st.rerun()

    tooltip = {"developer": "File paths, function names, types", "product": "Business behavior, plain English", "legal": "Policy clauses, audit-ready"}
    st.caption(f"*{tooltip[st.session_state['persona']]}*")

    # ── New conversation ──────────────────────────────────────
    st.write("")
    if st.button("＋ New Conversation", use_container_width=True, type="secondary"):
        st.session_state["messages"] = []
        st.rerun()

    # ── Domain browser ────────────────────────────────────────
    st.markdown("---")
    st.caption("Domains")

    with st.spinner(""):
        domains = api.get(f"/demo/repos/{new_repo_id}/domains")
    _ICONS = ["📦", "🔐", "💳", "👥", "⚙️", "🧩", "📡"]
    for i, domain in enumerate(domains):
        icon  = _ICONS[i % len(_ICONS)]
        label = f"{icon}  {domain['name']}  ({domain.get('member_count', 0)})"
        if st.button(label, key=f"d_{domain['id']}", use_container_width=True):
            prompt = f"Tell me about the {domain['name']} domain."
            st.session_state["messages"].append({"role": "user", "content": prompt})
            st.session_state["_pending_prompt"] = prompt
            st.rerun()

# ---------------------------------------------------------------------------
# Chat processing
# ---------------------------------------------------------------------------
def _process_chat(user_prompt: str):
    payload = {
        "message":  user_prompt,
        "repo_id":  st.session_state.get("selected_repo_id"),
        "persona":  st.session_state.get("persona", "developer"),
        "history":  st.session_state["messages"][:-1],
    }
    assistant_text = ""
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("▌")
        try:
            for event in api.stream("/demo/chat", json=payload):
                etype = event.get("event")
                data  = event.get("data", {})
                if etype == "tool_call":
                    if data.get("status") == "running":
                        st.markdown(f"<div class='cl-tool-call'>🔍 &nbsp;<code>{data.get('tool','')}</code></div>", unsafe_allow_html=True)
                    elif data.get("status") == "done":
                        st.markdown(f"<div class='cl-tool-done'>✅ &nbsp;{data.get('result_summary','Done')}</div>", unsafe_allow_html=True)
                elif etype == "token":
                    assistant_text += data.get("delta", "")
                    placeholder.markdown(assistant_text + "▌")
        except Exception as e:
            err = str(e).lower()
            if "rate" in err or "429" in err or "quota" in err:
                assistant_text = "⏳ Sending messages too quickly. Please wait ~30 seconds."
            elif "timeout" in err or "mcp" in err or "tool" in err:
                assistant_text = "❌ MCP tool timeout. Please try again."
            else:
                assistant_text = f"❌ Something went wrong. Please try again."
        placeholder.markdown(assistant_text)
    st.session_state["messages"].append({"role": "assistant", "content": assistant_text})

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.markdown("""
<div class="cl-page-header">
    <h1>Ask CodeLens</h1>
    <p>Ask anything about your codebase — structure, business rules, domain logic.</p>
</div>
""", unsafe_allow_html=True)

# Render history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Empty state
if not st.session_state["messages"]:
    st.markdown("""
    <div class="cl-chat-hero">
        <div class="cl-chat-hero-icon">◈</div>
        <h2>What would you like to know?</h2>
        <p>Ask about a function, explore a business domain,<br>or understand the rules behind any feature.</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    _suggestions = [
        ("🔍", "Explain a function",       "How does apply_discount work?"),
        ("🗂️", "Explore a domain",          "Tell me about the Checkout domain."),
        ("⚖️", "Understand business rules", "What are the discount rules in Payments?"),
    ]
    c1, c2, c3 = st.columns(3, gap="medium")
    for col, (icon, title, prompt) in zip([c1, c2, c3], _suggestions):
        with col:
            with st.container(border=True):
                st.markdown(f"<div style='font-size:1.6rem;margin-bottom:10px'>{icon}</div>", unsafe_allow_html=True)
                st.markdown(f"**{title}**")
                st.caption(f"*{prompt}*")
                st.write("")
                if st.button("Try this →", key=f"s_{hash(prompt)}", use_container_width=True):
                    st.session_state["messages"].append({"role": "user", "content": prompt})
                    st.session_state["_pending_prompt"] = prompt
                    st.rerun()

# Pending prompt (from domain buttons or suggestion cards)
if st.session_state.get("_pending_prompt"):
    pending = st.session_state.pop("_pending_prompt")
    with st.chat_message("user"):
        st.markdown(pending)
    _process_chat(pending)

# Live input
if prompt := st.chat_input("Ask about your codebase…"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    _process_chat(prompt)
