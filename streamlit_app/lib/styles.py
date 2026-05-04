import streamlit as st


def apply_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Material+Symbols+Sharp:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');

    /* ══════════════════════════════════════════════════════════
       BASE
    ══════════════════════════════════════════════════════════ */
    html, body, [class*="st-"], .stMarkdown, p, span, div,
    label, button, input, textarea, select {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    #MainMenu, footer, .stDeployButton { visibility: hidden; }
    .block-container { padding-top: 2.2rem !important; max-width: 1200px !important; }

    /* ── Material Symbols Sharp variable font fix ─────────────
       Without font-variation-settings the browser cannot render the glyphs
       and falls back to plain text (e.g. "keyboard_double_arrow_left").
       Setting the axes forces correct glyph rendering when the font loads.
       The visibility:hidden fallback hides the text while the font is absent
       and the ::after pseudo-element draws a CSS chevron instead.
    ──────────────────────────────────────────────────────── */
    .material-symbols-sharp {
        font-family: 'Material Symbols Sharp' !important;
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24 !important;
        -webkit-font-feature-settings: 'liga' !important;
        font-feature-settings: 'liga' !important;
        font-style: normal !important;
        font-weight: normal !important;
        text-rendering: optimizeLegibility !important;
    }

    /* ── Sidebar collapse / expand buttons ───────────────── */
    [data-testid*="ollapsed"] .material-symbols-sharp {
        font-size: 0 !important;
        display: inline-block !important;
        width: 20px !important; height: 20px !important;
        position: relative !important;
        visibility: visible !important;
    }
    [data-testid="collapsedControl"] .material-symbols-sharp::after {
        content: '◀' !important;
        font-size: 15px !important; font-family: sans-serif !important;
        color: #8892a4 !important; line-height: 1 !important;
        position: absolute !important;
        top: 50% !important; left: 50% !important;
        transform: translate(-50%, -50%) !important;
    }
    [data-testid="stSidebarCollapsedControl"] .material-symbols-sharp::after {
        content: '▶' !important;
        font-size: 15px !important; font-family: sans-serif !important;
        color: #8892a4 !important; line-height: 1 !important;
        position: absolute !important;
        top: 50% !important; left: 50% !important;
        transform: translate(-50%, -50%) !important;
    }

    /* ── Expander toggle arrows ───────────────────────────
       Streamlit 1.37+ renders st.expander with div[data-testid] wrappers,
       NOT native <details>/<summary>. Target the icon wrapper directly. */

    /* Hide the raw "arrow_right" / "expand_more" icon-name text */
    [data-testid="stExpanderToggleIcon"] .material-symbols-sharp,
    [data-testid="stExpanderToggleIcon"] span {
        font-size: 0 !important;
        line-height: 0 !important;
        color: transparent !important;
        display: inline-block !important;
        width: 16px !important; height: 16px !important;
        position: relative !important;
        overflow: hidden !important;
    }

    /* Collapsed state → ▸ */
    [data-testid="stExpanderToggleIcon"] .material-symbols-sharp::after,
    [data-testid="stExpanderToggleIcon"] span::after {
        content: '▸' !important;
        font-size: 13px !important;
        font-family: sans-serif !important;
        color: #8892a4 !important;
        line-height: 1 !important;
        overflow: visible !important;
        position: absolute !important;
        top: 50% !important; left: 50% !important;
        transform: translate(-50%, -50%) !important;
    }

    /* Open state — Streamlit adds a CSS rotation to the icon wrapper */
    [data-testid="stExpanderToggleIcon"][style*="rotate"] .material-symbols-sharp::after,
    [data-testid="stExpanderToggleIcon"][style*="rotate"] span::after,
    [aria-expanded="true"] [data-testid="stExpanderToggleIcon"] .material-symbols-sharp::after,
    [aria-expanded="true"] [data-testid="stExpanderToggleIcon"] span::after {
        content: '▾' !important;
    }

    /* Hide Streamlit's built-in prev/next page navigation arrows */
    [data-testid="stPageLink"],
    [data-testid="stPageNavigation"],
    [data-testid="stBottomNavigation"],
    button[kind="pageNavigation"],
    .stPageLink { display: none !important; }

    /* ══════════════════════════════════════════════════════════
       SIDEBAR FLEX LAYOUT — footer sticks to bottom
    ══════════════════════════════════════════════════════════ */
    /* Make the sidebar's inner content block a flex column */
    [data-testid="stSidebarContent"] > [data-testid="stVerticalBlock"] {
        min-height: 100vh !important;
        display: flex !important;
        flex-direction: column !important;
    }
    /* Spacer grows to fill remaining space between nav and footer */
    .cl-sidebar-spacer {
        flex: 1 1 auto !important;
        min-height: 24px !important;
    }
    /* Footer sits flush at bottom */
    .cl-sidebar-footer {
        border-top: 1px solid #1a2236;
        padding-top: 10px;
        padding-bottom: 4px;
    }

    /* ══════════════════════════════════════════════════════════
       SIDEBAR
    ══════════════════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: #080D1A !important;
        border-right: 1px solid #1a2236 !important;
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

    /* Navigation links */
    [data-testid="stSidebarNavLink"] {
        border-radius: 8px !important;
        margin: 2px 6px !important;
        color: #8892a4 !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        transition: background 0.15s, color 0.15s !important;
    }
    [data-testid="stSidebarNavLink"]:hover {
        background: rgba(99,102,241,.12) !important;
        color: #c4cdff !important;
    }
    [data-testid="stSidebarNavLink"][aria-selected="true"] {
        background: rgba(99,102,241,.2) !important;
        color: #a5b4fc !important;
        font-weight: 600 !important;
    }

    /* Sidebar section separators */
    [data-testid="stSidebarNavSeparatorHeader"] {
        font-size: 10px !important;
        letter-spacing: .12em !important;
        text-transform: uppercase !important;
        color: #2d3748 !important;
        font-weight: 700 !important;
        padding-left: 18px !important;
    }

    /* Sidebar caption / small text */
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #4b5563 !important;
        font-size: 12px !important;
    }

    /* Domain buttons in sidebar: plain text style */
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #1a2236 !important;
        color: #6b7280 !important;
        font-size: 13px !important;
        padding: 7px 12px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        border-radius: 7px !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: rgba(99,102,241,.1) !important;
        border-color: rgba(99,102,241,.3) !important;
        color: #a5b4fc !important;
    }

    /* ══════════════════════════════════════════════════════════
       BUTTONS
    ══════════════════════════════════════════════════════════ */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: -.01em !important;
        transition: all .18s ease !important;
        padding: 8px 16px !important;
    }

    /* Primary */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg,#4f46e5 0%,#6366f1 100%) !important;
        color: #fff !important;
        border: none !important;
        box-shadow: 0 1px 3px rgba(99,102,241,.35), 0 4px 12px rgba(99,102,241,.18) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg,#4338ca 0%,#4f46e5 100%) !important;
        box-shadow: 0 2px 8px rgba(99,102,241,.5), 0 6px 20px rgba(99,102,241,.25) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="primary"]:active { transform: translateY(0) !important; }

    /* Secondary */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #2d3748 !important;
        color: #8892a4 !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #1a2235 !important;
        border-color: #4b5563 !important;
        color: #e2e8f0 !important;
    }

    /* ══════════════════════════════════════════════════════════
       INPUTS
    ══════════════════════════════════════════════════════════ */
    .stTextInput input,
    .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid #2d3748 !important;
        background: #111827 !important;
        color: #f1f5f9 !important;
        font-size: 14px !important;
        transition: border-color .2s, box-shadow .2s !important;
    }
    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,.15) !important;
        outline: none !important;
    }
    .stSelectbox > div[data-baseweb="select"] > div {
        border-radius: 8px !important;
        border: 1px solid #2d3748 !important;
        background: #111827 !important;
        color: #f1f5f9 !important;
    }
    /* Input and selectbox labels */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stRadio label { color: #9ca3af !important; font-size: 13px !important; font-weight: 500 !important; }

    /* Captions / small text */
    .stCaption, [data-testid="stCaptionContainer"] p {
        color: #6b7280 !important;
        font-size: 12px !important;
    }

    /* Radio buttons */
    .stRadio [data-baseweb="radio"] label { color: #d1d5db !important; font-size: 14px !important; }

    /* Dataframe header */
    [data-testid="stDataFrame"] th {
        background: #1a2236 !important;
        color: #9ca3af !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        letter-spacing: .05em !important;
        text-transform: uppercase !important;
    }
    [data-testid="stDataFrame"] td { color: #d1d5db !important; font-size: 13px !important; }

    /* ══════════════════════════════════════════════════════════
       METRICS
    ══════════════════════════════════════════════════════════ */
    [data-testid="stMetric"] {
        background: #111827 !important;
        border: 1px solid #1a2236 !important;
        border-radius: 14px !important;
        padding: 20px 22px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    [data-testid="stMetric"]::after {
        content: '' !important;
        position: absolute !important;
        top: 0; left: 0; right: 0;
        height: 2px !important;
        background: linear-gradient(90deg,#6366f1,#818cf8) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        letter-spacing: -.03em !important;
        color: #f9fafb !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 11px !important;
        font-weight: 600 !important;
        letter-spacing: .08em !important;
        text-transform: uppercase !important;
        color: #4b5563 !important;
    }

    /* ══════════════════════════════════════════════════════════
       CONTAINERS (border=True)
    ══════════════════════════════════════════════════════════ */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #111827 !important;
        border: 1px solid #1a2236 !important;
        border-radius: 14px !important;
        padding: 4px !important;
        transition: border-color .2s !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(99,102,241,.35) !important;
    }

    /* ══════════════════════════════════════════════════════════
       DATAFRAME
    ══════════════════════════════════════════════════════════ */
    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid #1a2236 !important;
    }

    /* ══════════════════════════════════════════════════════════
       CHAT
    ══════════════════════════════════════════════════════════ */
    [data-testid="stChatMessage"] {
        background: #111827 !important;
        border: 1px solid #1a2236 !important;
        border-radius: 14px !important;
        padding: 16px 20px !important;
        margin: 5px 0 !important;
    }

    /* Chat input box */
    [data-testid="stChatInput"] {
        border-top: 1px solid #1a2236 !important;
        background: #0f172a !important;
        padding: 12px 0 !important;
    }
    [data-testid="stChatInput"] textarea {
        border-radius: 12px !important;
        border: 1px solid #2d3748 !important;
        background: #111827 !important;
        color: #f1f5f9 !important;
        font-size: 15px !important;
        padding: 14px 16px !important;
        transition: border-color .2s, box-shadow .2s !important;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,.12) !important;
    }

    /* ══════════════════════════════════════════════════════════
       FORMS
    ══════════════════════════════════════════════════════════ */
    [data-testid="stForm"] {
        border: 1px solid #1a2236 !important;
        border-radius: 14px !important;
        background: #111827 !important;
        padding: 20px !important;
    }

    /* ══════════════════════════════════════════════════════════
       EXPANDER
    ══════════════════════════════════════════════════════════ */
    [data-testid="stExpander"] {
        border: 1px solid #1a2236 !important;
        border-radius: 10px !important;
        background: #111827 !important;
    }
    [data-testid="stExpander"] summary {
        font-size: 14px !important;
        font-weight: 500 !important;
    }

    /* ══════════════════════════════════════════════════════════
       MISC
    ══════════════════════════════════════════════════════════ */
    /* Hide "Press Enter to submit" hint inside forms */
    [data-testid="InputInstructions"] { display: none !important; }

    hr { border-color: #1a2236 !important; margin: 16px 0 !important; }

    [data-testid="stAlertContainer"] { border-radius: 10px !important; }

    /* Toast */
    [data-testid="stToast"] {
        border-radius: 10px !important;
        border: 1px solid #1a2236 !important;
        background: #111827 !important;
    }

    /* Dialog */
    [data-testid="stModal"] > div > div {
        background: #111827 !important;
        border: 1px solid #1a2236 !important;
        border-radius: 16px !important;
    }

    /* ══════════════════════════════════════════════════════════
       CUSTOM COMPONENTS (HTML injected via st.markdown)
    ══════════════════════════════════════════════════════════ */

    /* Page header */
    .cl-page-header { margin-bottom: 24px; }
    .cl-page-header h1 {
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -.03em;
        margin: 0 0 4px;
        background: linear-gradient(135deg,#f9fafb 40%,#818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .cl-page-header p { color: #4b5563; font-size: 14px; margin: 0; }

    /* Sidebar brand */
    .cl-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 18px 14px 14px;
        border-bottom: 1px solid #1a2236;
        margin-bottom: 6px;
    }
    .cl-brand-icon {
        width: 30px; height: 30px;
        background: linear-gradient(135deg,#4f46e5,#818cf8);
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 15px; flex-shrink: 0;
    }
    .cl-brand-name {
        font-size: 15px; font-weight: 700;
        letter-spacing: -.02em;
        color: #f9fafb !important;
    }

    /* User info */
    .cl-user-info {
        padding: 10px 12px;
        background: #0d1117;
        border: 1px solid #1a2236;
        border-radius: 10px;
        margin: 2px 4px;
    }
    .cl-user-email { font-size: 12px; color: #6b7280; font-weight: 500; }
    .cl-role-badge {
        display: inline-block;
        background: rgba(99,102,241,.18);
        color: #818cf8;
        border-radius: 4px;
        padding: 1px 7px;
        font-size: 10px; font-weight: 700;
        letter-spacing: .06em;
        text-transform: uppercase;
        margin-top: 3px;
    }

    /* Chat hero (empty state) */
    .cl-chat-hero {
        text-align: center;
        padding: 52px 20px 36px;
    }
    .cl-chat-hero-icon {
        width: 60px; height: 60px;
        background: linear-gradient(135deg,#4f46e5,#818cf8);
        border-radius: 16px;
        display: flex; align-items: center; justify-content: center;
        font-size: 26px;
        margin: 0 auto 18px;
        box-shadow: 0 8px 28px rgba(99,102,241,.35);
    }
    .cl-chat-hero h2 {
        font-size: 1.75rem; font-weight: 700;
        letter-spacing: -.03em;
        color: #f9fafb; margin: 0 0 10px;
    }
    .cl-chat-hero p { color: #4b5563; font-size: 15px; line-height: 1.6; margin: 0; }

    /* Login page */
    .cl-login-logo {
        width: 52px; height: 52px;
        background: linear-gradient(135deg,#4f46e5,#818cf8);
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-size: 24px;
        margin: 0 auto 16px;
        box-shadow: 0 8px 28px rgba(99,102,241,.4);
    }
    .cl-login-title {
        font-size: 2.1rem; font-weight: 800;
        letter-spacing: -.04em;
        background: linear-gradient(135deg,#f9fafb 40%,#818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center; margin-bottom: 6px;
    }
    .cl-login-sub { color: #4b5563; font-size: 15px; text-align: center; margin-bottom: 28px; }
    .cl-login-hint { text-align: center; margin-top: 14px; font-size: 13px; color: #374151; }
    .cl-login-hint code {
        background: #1e293b;
        border: 1px solid #2d3748;
        border-radius: 5px;
        padding: 1px 6px;
        font-family: 'SF Mono','Fira Code',monospace;
        color: #818cf8; font-size: 12px;
    }

    /* Tool call lines in chat */
    .cl-tool-call {
        font-size: 13px; color: #4b5563;
        padding: 4px 0 2px;
        border-left: 2px solid #374151;
        padding-left: 10px;
        margin: 4px 0;
    }
    .cl-tool-done {
        font-size: 13px; color: #34d399;
        padding: 2px 0 6px;
        border-left: 2px solid #34d399;
        padding-left: 10px;
        margin: 2px 0;
    }
    </style>
    """, unsafe_allow_html=True)
