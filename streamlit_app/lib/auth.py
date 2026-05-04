import streamlit as st


def require_login():
    if not st.session_state.get("token"):
        # Home.py is the main script — st.switch_page("Home.py") is unsupported
        # in Streamlit 1.37+. Rerun instead; Home.py will show the login form.
        st.rerun()


def require_admin():
    require_login()
    if st.session_state.get("role") != "admin":
        st.error("Access denied. Admin privileges required.")
        st.stop()


def logout():
    import lib.api_client as api
    try:
        api.post("/auth/logout")
    except Exception:
        pass
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
