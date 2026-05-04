import streamlit as st

# Read auth state before set_page_config (session_state is safe to read first)
_logged_in = bool(st.session_state.get("token"))

st.set_page_config(
    page_title="CodeLens",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded" if _logged_in else "collapsed",
)

import lib.api_client as api
from lib.auth import logout
from lib.styles import apply_styles

apply_styles()

# ---------------------------------------------------------------------------
# Login forms
# ---------------------------------------------------------------------------

def _login_form():
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;padding:40px 0 28px">
            <div class="cl-login-logo">◈</div>
            <div class="cl-login-title">CodeLens</div>
            <div class="cl-login-sub">Code Intelligence Platform</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", border=True):
            email = st.text_input("Username", placeholder="user  or  admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button(
                "Sign In →", type="primary", use_container_width=True
            )

        if submitted:
            if not email or not password:
                st.error("Enter your credentials.")
                return
            try:
                with st.spinner(""):
                    result = api.login(email.strip(), password)
            except ValueError as e:
                st.error(str(e))
                return

            st.session_state["token"] = result["token"]
            st.session_state["user_id"] = result["user_id"]
            st.session_state["email"] = result["email"]
            st.session_state["role"] = result["role"]
            st.session_state["must_change_password"] = result.get("must_change_password", False)
            st.rerun()

        st.markdown("""
        <div class="cl-login-hint">
            <code>user</code> / <code>user</code> &nbsp;·&nbsp;
            <code>admin</code> / <code>admin</code>
        </div>
        """, unsafe_allow_html=True)


def _change_password_form():
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;padding:40px 0 20px">
            <div class="cl-login-logo">🔒</div>
            <div class="cl-login-title" style="font-size:1.6rem">Change Password</div>
            <div class="cl-login-sub">Set a new password to continue.</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("change_password_form", border=True):
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button(
                "Set Password →", type="primary", use_container_width=True
            )

        if submitted:
            if new_pw != confirm_pw:
                st.error("Passwords do not match.")
                return
            if len(new_pw) < 8:
                st.error("Password must be at least 8 characters.")
                return
            with st.spinner(""):
                result = api.post("/auth/change-password", json={"new_password": new_pw})
            st.session_state["token"] = result["token"]
            st.session_state["must_change_password"] = False
            st.toast("Password updated.", icon="✓")
            st.rerun()


# ---------------------------------------------------------------------------
# Authenticated app shell with role-based navigation
# ---------------------------------------------------------------------------

def _run_app():
    ask_page       = st.Page("pages/1_Ask.py",              title="Ask CodeLens",  icon="💬", default=True)
    dashboard_page = st.Page("pages/2_Admin_Dashboard.py",  title="Dashboard",     icon="📊")
    repos_page     = st.Page("pages/3_Admin_Repos.py",      title="Repositories",  icon="🗂️")
    domains_page   = st.Page("pages/4_Admin_Domains.py",    title="Domains",       icon="🔬")
    users_page     = st.Page("pages/5_Admin_Users.py",      title="Users",         icon="👥")

    role = st.session_state.get("role", "user")
    nav_pages = (
        {"": [ask_page], "Admin": [dashboard_page, repos_page, domains_page, users_page]}
        if role == "admin"
        else {"": [ask_page]}
    )

    with st.sidebar:
        st.markdown("""
        <div class="cl-brand">
            <div class="cl-brand-icon">◈</div>
            <span class="cl-brand-name">CodeLens</span>
        </div>
        """, unsafe_allow_html=True)

    pg = st.navigation(nav_pages)

    # Run the active page FIRST so its sidebar content renders before the footer.
    pg.run()

    # Footer always appears after all page-specific sidebar content.
    with st.sidebar:
        st.markdown('<div class="cl-sidebar-spacer"></div>', unsafe_allow_html=True)
        role_label = "Admin" if role == "admin" else "User"
        st.markdown(f"""
        <div class="cl-sidebar-footer">
            <div class="cl-user-info">
                <div class="cl-user-email">{st.session_state.get('email', '')}</div>
                <div style="margin-top:4px"><span class="cl-role-badge">{role_label}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True, key="sidebar_logout"):
            logout()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if not _logged_in:
    # Hide sidebar and its toggle button entirely on the login screen.
    # The pages/ auto-discovery still runs but is invisible; each page
    # has its own require_login() / require_admin() guard anyway.
    st.markdown("""<style>
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"] { display: none !important; }
    </style>""", unsafe_allow_html=True)
    if st.session_state.get("must_change_password"):
        _change_password_form()
    else:
        _login_form()
else:
    _run_app()
