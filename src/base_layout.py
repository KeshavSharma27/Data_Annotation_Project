import streamlit as st



COLORS = {
    # Brand
    "primary":        "#2563EB",   # blue – buttons, links, active states
    "primary_hover":  "#1D4ED8",   # darker blue on hover

    # Text
    "text_primary":   "#111827",   # headings and body copy
    "text_secondary": "#6B7280",   # subtitles, descriptions, meta
    "text_muted":     "#9CA3AF",   # placeholders, disabled

    # Surfaces
    "page_bg":        "#F8FAFC",   # outer page background
    "card_bg":        "#FFFFFF",   # white cards
    "border":         "#E5E7EB",   # subtle borders

    # Status
    "success":        "#10B981",   # green  – completed
    "warning":        "#F59E0B",   # amber  – in progress / pending
    "error":          "#EF4444",   # red    – failed / error

    # Badge backgrounds (light tints of status colors)
    "success_bg":     "#ECFDF5",
    "warning_bg":     "#FFFBEB",
    "error_bg":       "#FEF2F2",
}

FONTS = {
    "sans": "'Inter', 'Segoe UI', 'Source Sans Pro', system-ui, sans-serif",
}

SPACING = {
    
    "xs":  "8px",
    "sm":  "16px",
    "md":  "24px",
    "lg":  "32px",
    "xl":  "48px",
}

SHADOWS = {
    "card": "0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)",
    "card_hover": "0 4px 12px rgba(0, 0, 0, 0.10)",
}


def _build_css() -> str:
    return f"""
    <style>
   
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {{
        --color-primary:       {COLORS['primary']};
        --color-primary-hover: {COLORS['primary_hover']};
        --color-text-primary:  {COLORS['text_primary']};
        --color-text-secondary:{COLORS['text_secondary']};
        --color-text-muted:    {COLORS['text_muted']};
        --color-page-bg:       {COLORS['page_bg']};
        --color-card-bg:       {COLORS['card_bg']};
        --color-border:        {COLORS['border']};
        --color-success:       {COLORS['success']};
        --color-warning:       {COLORS['warning']};
        --color-error:         {COLORS['error']};

        --font-sans:  {FONTS['sans']};

        --space-xs:  {SPACING['xs']};
        --space-sm:  {SPACING['sm']};
        --space-md:  {SPACING['md']};
        --space-lg:  {SPACING['lg']};
        --space-xl:  {SPACING['xl']};

        --shadow-card:       {SHADOWS['card']};
        --shadow-card-hover: {SHADOWS['card_hover']};

        --radius-card:   12px;
        --radius-badge:  6px;
        --radius-input:  8px;

        --max-width: 1280px;
    }}

    /* ── Reset Streamlit's default page background ──────────────────────── */
    .stApp {{
        background-color: var(--color-page-bg) !important;
        font-family: var(--font-sans) !important;
    }}

    /* Hide Streamlit's default top padding and the "Made with Streamlit" footer */
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        max-width: var(--max-width) !important;
    }}

    /* ── Typography ─────────────────────────────────────────────────────── */
    h1, h2, h3, h4, p, span, div {{
        font-family: var(--font-sans) !important;
    }}

    /* ── Card component ─────────────────────────────────────────────────── */
    /*
       .ls-card is the base class for every white content section.
       homescreen.py wraps content in st.markdown('<div class="ls-card">…</div>').
    */
    .ls-card {{
        background:    var(--color-card-bg);
        border:        1px solid var(--color-border);
        border-radius: var(--radius-card);
        padding:       var(--space-md);
        box-shadow:    var(--shadow-card);
        margin-bottom: var(--space-md);
    }}

    /* ── Section header (title + description inside a card) ─────────────── */
    .ls-section-title {{
        font-size:   18px;
        font-weight: 600;
        color:       var(--color-text-primary);
        margin:      0 0 4px 0;
        line-height: 1.4;
    }}

    .ls-section-desc {{
        font-size:   14px;
        color:       var(--color-text-secondary);
        margin:      0 0 var(--space-sm) 0;
        line-height: 1.5;
    }}

    /* ── Page header (the big title at the very top) ─────────────────────── */
    .ls-page-title {{
        font-size:   32px;
        font-weight: 700;
        color:       var(--color-text-primary);
        margin:      0 0 6px 0;
        letter-spacing: -0.5px;
    }}

    .ls-page-subtitle {{
        font-size:   16px;
        font-weight: 400;
        color:       var(--color-text-secondary);
        margin:      0 0 var(--space-lg) 0;
    }}

    /* ── Divider ─────────────────────────────────────────────────────────── */
    .ls-divider {{
        border: none;
        border-top: 1px solid var(--color-border);
        margin: var(--space-sm) 0;
    }}

    /* ── Project card (used in the Available Projects grid) ─────────────── */
    .ls-project-card {{
        background:    var(--color-card-bg);
        border:        1px solid var(--color-border);
        border-radius: var(--radius-card);
        padding:       var(--space-sm) var(--space-md);
        box-shadow:    var(--shadow-card);
        transition:    box-shadow 0.15s ease, border-color 0.15s ease;
        cursor:        pointer;
        margin-bottom: var(--space-xs);
    }}

    .ls-project-card:hover {{
        box-shadow:    var(--shadow-card-hover);
        border-color:  var(--color-primary);
    }}

    .ls-project-card-title {{
        font-size:   15px;
        font-weight: 600;
        color:       var(--color-text-primary);
        margin:      0 0 4px 0;
    }}

    .ls-project-card-meta {{
        font-size:  13px;
        color:      var(--color-text-secondary);
        margin:     0;
    }}

    /* ── Stat card (used in Project Overview grid) ───────────────────────── */
    .ls-stat-card {{
        background:    var(--color-card-bg);
        border:        1px solid var(--color-border);
        border-radius: var(--radius-card);
        padding:       var(--space-sm) var(--space-md);
        box-shadow:    var(--shadow-card);
        text-align:    left;
    }}

    .ls-stat-label {{
        font-size:   12px;
        font-weight: 500;
        color:       var(--color-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin:      0 0 6px 0;
    }}

    .ls-stat-value {{
        font-size:   28px;
        font-weight: 700;
        color:       var(--color-text-primary);
        margin:      0;
        line-height: 1;
    }}

    .ls-stat-sub {{
        font-size:  12px;
        color:      var(--color-text-muted);
        margin:     4px 0 0 0;
    }}

    /* ── Status badge ────────────────────────────────────────────────────── */
    .ls-badge {{
        display:       inline-block;
        font-size:     12px;
        font-weight:   500;
        padding:       2px 8px;
        border-radius: var(--radius-badge);
        line-height:   1.6;
    }}

    .ls-badge-success {{
        background: {COLORS['success_bg']};
        color:      {COLORS['success']};
    }}

    .ls-badge-warning {{
        background: {COLORS['warning_bg']};
        color:      {COLORS['warning']};
    }}

    .ls-badge-error {{
        background: {COLORS['error_bg']};
        color:      {COLORS['error']};
    }}

    /* ── Task table wrapper ──────────────────────────────────────────────── */
    /*
       Streamlit's st.dataframe renders inside its own container.
       .ls-table-wrapper is a card around it for visual consistency.
    */
    .ls-table-wrapper {{
        background:    var(--color-card-bg);
        border:        1px solid var(--color-border);
        border-radius: var(--radius-card);
        padding:       var(--space-md);
        box-shadow:    var(--shadow-card);
    }}

    /* ── Streamlit widget overrides ──────────────────────────────────────── */

    /* Text input */
    .stTextInput > div > div > input {{
        border:        1px solid var(--color-border) !important;
        border-radius: var(--radius-input) !important;
        font-family:   var(--font-sans) !important;
        font-size:     14px !important;
        background:black;
        color: white !important;
        -webkit-text-fill-color: white !important;
        opacity: 1 !important;
        padding:       10px 12px !important;
    }}

    .stTextInput > div > div > input:focus {{
        border-color: var(--color-primary) !important;
        box-shadow:   0 0 0 3px rgba(37, 99, 235, 0.12) !important;
        background:black;
        outline:      none !important;
    }}

    /* Selectbox */
    .stSelectbox > div > div {{
        border:        1px solid var(--color-border) !important;
        border-radius: var(--radius-input) !important;
        font-family:   var(--font-sans) !important;
        font-size:     14px !important;
    }}

    /* Primary button */
    .stButton > button[kind="primary"] {{
        background:    var(--color-primary) !important;
        border:        none !important;
        border-radius: var(--radius-input) !important;
        color:         #ffffff !important;
        font-family:   var(--font-sans) !important;
        font-size:     14px !important;
        font-weight:   500 !important;
        padding:       10px 20px !important;
        transition:    background 0.15s ease !important;
    }}

    .stButton > button[kind="primary"]:hover {{
        background: var(--color-primary-hover) !important;
    }}

    /* Secondary / default button */
    .stButton > button {{
        border:        1px solid var(--color-border) !important;
        border-radius: var(--radius-input) !important;
        font-family:   var(--font-sans) !important;
        font-size:     14px !important;
        font-weight:   500 !important;
        padding:       8px 16px !important;
        transition:    background 0.15s ease, border-color 0.15s ease !important;
    }}

    /* Streamlit dataframe */
    .stDataFrame {{
        border-radius: 8px !important;
        overflow:      hidden !important;
    }}

    /* Alert / info boxes */
    .stAlert {{
        border-radius: var(--radius-card) !important;
        font-family:   var(--font-sans) !important;
        font-size:     14px !important;
    }}

    /* Spinner text */
    .stSpinner > div {{
        font-family: var(--font-sans) !important;
        color:       var(--color-text-secondary) !important;
    }}
    </style>
    """


def apply_base_styles() -> None:
    """
    Call this ONCE at the very top of homescreen.py (before any other st.* call).
    It injects the global CSS and sets the Streamlit page config defaults.
    """
    st.markdown(_build_css(), unsafe_allow_html=True)




def render_page_header() -> str:
    """
    Returns the top-of-page title and subtitle HTML.
    Displayed once at the top of homescreen.py.
    """
    return """
    <div>
        <p class="ls-page-title">Label Studio Dashboard</p>
        <p class="ls-page-subtitle">
            Connect your Label Studio workspace and explore project insights.
        </p>
    </div>
    """






def render_section_header(title: str, description: str) -> str:
    """
    Returns a section title + description block.
    Used at the top of every card section.

    Args:
        title:       Bold heading text.
        description: Muted subtitle text below the heading.
    """
    return f"""
    <div>
        <p class="ls-section-title">{title}</p>
        <p class="ls-section-desc">{description}</p>
        <hr class="ls-divider">
    </div>
    """


def render_project_card(
    title: str,
    task_count: int,
    annotated: int,
    created_at: str,
    project_id: int,
) -> str:
    """
    Returns HTML for a single project card shown in the Available Projects grid.

    Args:
        title:       Project name.
        task_count:  Total number of tasks in the project.
        annotated:   Number of tasks that have been annotated.
        created_at:  ISO date string (we only show the date part, e.g. "2024-06-01").
        project_id:  Numeric Label Studio project ID.
    """
    return f"""
    <div class="ls-project-card">
        <p class="ls-project-card-title">{title}</p>
        <p class="ls-project-card-meta">
            📋 {task_count} tasks &nbsp;·&nbsp;
            ✅ {annotated} annotated &nbsp;·&nbsp;
            🗓 {created_at[:10]}
        </p>
        <p class="ls-project-card-meta" style="color: #9CA3AF; font-size:12px; margin-top:4px;">
            ID: {project_id}
        </p>
    </div>
    """


def render_stat_card(label: str, value: str, sub: str = "") -> str:
    """
    Returns HTML for a single statistic card in the Project Overview grid.

    Args:
        label: Short uppercase label, e.g. "Total Tasks".
        value: The big number or string to display prominently.
        sub:   Optional small note below the value, e.g. "across all projects".
    """
    sub_html = f'<p class="ls-stat-sub">{sub}</p>' if sub else ""
    return f"""
    <div class="ls-stat-card">
        <p class="ls-stat-label">{label}</p>
        <p class="ls-stat-value">{value}</p>
        {sub_html}
    </div>
    """


def render_status_badge(status: str) -> str:
    """
    Returns an inline HTML status badge.

    Args:
        status: One of "Completed", "Pending", or "Error".
                Anything else renders as a neutral grey badge.
    """
    status_lower = status.lower()
    if status_lower == "completed":
        css_class = "ls-badge-success"
    elif status_lower == "pending":
        css_class = "ls-badge-warning"
    elif status_lower == "error":
        css_class = "ls-badge-error"
    else:
        css_class = ""   # plain unstyled badge

    return f'<span class="ls-badge {css_class}">{status}</span>'


def render_empty_state(icon: str, heading: str, body: str) -> str:
    """
    Returns a centred empty-state placeholder block.
    Used when there are no projects or no tasks to show yet.

    Args:
        icon:    An emoji or icon character.
        heading: Short bold message, e.g. "No projects found".
        body:    Longer helpful explanation.
    """
    return f"""
    <div style="
        text-align: center;
        padding: 48px 24px;
        color: {COLORS['text_secondary']};
    ">
        <div style="font-size: 40px; margin-bottom: 12px;">{icon}</div>
        <p style="
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            margin: 0 0 6px 0;
        ">{heading}</p>
        <p style="font-size: 14px; margin: 0;">{body}</p>
    </div>
    """


def render_error_banner(message: str) -> str:
    """
    Returns a red error notice block.

    Args:
        message: The error message to display.
    """
    return f"""
    <div style="
        background: {COLORS['error_bg']};
        border: 1px solid {COLORS['error']};
        border-radius: 8px;
        padding: 12px 16px;
        color: {COLORS['error']};
        font-size: 14px;
        margin-bottom: 16px;
    ">
        ⚠️ &nbsp; {message}
    </div>
    """
