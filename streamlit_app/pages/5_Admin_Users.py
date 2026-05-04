import streamlit as st

import lib.api_client as api
from lib.auth import require_admin

require_admin()


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

@st.dialog("Add User")
def _add_user_dialog():
    if "new_user_temp_password" not in st.session_state:
        with st.form("add_user_form"):
            email = st.text_input("Email address")
            role = st.radio("Role", ["user", "admin"], horizontal=True)
            submitted = st.form_submit_button("Create User", type="primary")
        if submitted:
            if not email or "@" not in email:
                st.error("Enter a valid email address.")
                return
            with st.spinner("Creating…"):
                result = api.post("/admin/users", json={"email": email, "role": role})
            st.session_state["new_user_temp_password"] = result.get("temporary_password", "")
            st.rerun()
    else:
        temp_pw = st.session_state["new_user_temp_password"]
        st.success("User created.")
        st.warning("⚠️ This password is shown **once only**. Copy it now.")
        st.code(temp_pw, language=None)
        if st.button("Done", type="primary", use_container_width=True):
            del st.session_state["new_user_temp_password"]
            st.rerun()


@st.dialog("Reset Password")
def _reset_password_dialog():
    user = st.session_state.get("_reset_password_target", {})
    if "reset_temp_password" not in st.session_state:
        st.write(f"Reset password for **{user.get('email')}**?")
        c1, c2 = st.columns(2)
        if c1.button("Cancel", use_container_width=True):
            st.session_state.pop("_reset_password_target", None)
            st.rerun()
        if c2.button("Reset", type="primary", use_container_width=True):
            with st.spinner("Resetting…"):
                result = api.post(f"/admin/users/{user['id']}/reset-password")
            st.session_state["reset_temp_password"] = result.get("temporary_password", "")
            st.rerun()
    else:
        temp_pw = st.session_state["reset_temp_password"]
        st.success(f"Password reset for **{user.get('email')}**.")
        st.warning("⚠️ This password is shown **once only**. Copy it now.")
        st.code(temp_pw, language=None)
        if st.button("Done", type="primary", use_container_width=True):
            del st.session_state["reset_temp_password"]
            st.session_state.pop("_reset_password_target", None)
            st.rerun()


@st.dialog("Confirm Delete User")
def _confirm_delete_user_dialog():
    user = st.session_state.get("_delete_user_target", {})
    st.markdown(f"Delete **{user.get('email')}**?")
    st.caption("This action cannot be undone.")
    c1, c2 = st.columns(2)
    if c1.button("Cancel", use_container_width=True):
        st.session_state.pop("_delete_user_target", None)
        st.rerun()
    if c2.button("Delete", type="primary", use_container_width=True):
        with st.spinner("Deleting…"):
            api.delete(f"/admin/users/{user['id']}")
        st.session_state.pop("_delete_user_target", None)
        st.toast(f"User '{user.get('email')}' deleted.", icon="✓")
        st.rerun()


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

hdr, btn_col = st.columns([5, 1])
hdr.markdown("""
<div class="cl-page-header">
    <h1>Users</h1>
    <p>Manage access and roles</p>
</div>
""", unsafe_allow_html=True)
with btn_col:
    st.write("")
    st.write("")
    if st.button("＋ Add User", type="primary", use_container_width=True):
        _add_user_dialog()

with st.spinner(""):
    users = api.get("/admin/users")

if not users:
    st.info("No users found.")
else:
    current_user_id = st.session_state.get("user_id")

    for user in users:
        is_self = user["id"] == current_user_id
        with st.container(border=True):
            info_col, actions_col = st.columns([4, 3])

            with info_col:
                you_tag = " <span style='color:#4B5563;font-size:12px'>(you)</span>" if is_self else ""
                role_color = "#818CF8" if user["role"] == "admin" else "#4B5563"
                mcp_badge = " <span style='background:#3B1F1F;color:#F87171;border-radius:4px;padding:1px 6px;font-size:10px;font-weight:600'>MUST CHANGE PW</span>" if user.get("must_change_password") else ""
                st.markdown(
                    f"**{user['email']}**{you_tag}"
                    f"&nbsp;&nbsp;<span style='background:rgba(99,102,241,.15);color:{role_color};"
                    f"border-radius:4px;padding:1px 8px;font-size:11px;font-weight:600'>"
                    f"{user['role'].upper()}</span>{mcp_badge}",
                    unsafe_allow_html=True,
                )
                joined = (user.get("created_at") or "")[:10]
                last   = user.get("last_login") or "Never"
                st.caption(f"Joined: {joined} · Last login: {last}")

            with actions_col:
                a1, a2, a3 = st.columns(3)

                promote_label = "Revoke Admin" if user["role"] == "admin" else "Make Admin"
                if a1.button(promote_label, key=f"promote_{user['id']}", disabled=is_self, use_container_width=True):
                    new_role = "user" if user["role"] == "admin" else "admin"
                    with st.spinner(""):
                        api.patch(f"/admin/users/{user['id']}", json={"role": new_role})
                    st.toast("Role updated.", icon="✓")
                    st.rerun()

                if a2.button("Reset PW", key=f"reset_{user['id']}", use_container_width=True):
                    st.session_state["_reset_password_target"] = user
                    _reset_password_dialog()

                if a3.button("Delete", key=f"delete_user_{user['id']}", disabled=is_self, use_container_width=True):
                    st.session_state["_delete_user_target"] = user
                    _confirm_delete_user_dialog()
