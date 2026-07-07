from __future__ import annotations
import streamlit as st
import requests
import src.base_layout as layout
from backend.retrieve_task import (
    ALL_COLUMNS,
    DEFAULT_COLUMNS,
    build_tasks_dataframe,
    fetch_projects,
    fetch_reviews,
    fetch_tasks,
    store_mongodb,
)
import streamlit.components.v1 as components
import subprocess
import sys
import time
import os
from dotenv import load_dotenv

load_dotenv()
mongodb_url = os.getenv("MONGODB_TOKEN")


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))       # .../Desktop/Data Annotation
_DESKTOP_DIR = os.path.dirname(_THIS_DIR)                     # .../Desktop
CHATBOT_APP_FILE = os.path.join(_DESKTOP_DIR, "chatbot", "application.py")
CHATBOT_APP_PORT = 8502


def start_backend(module_path: str, host: str, port: int, label: str) -> None:

    probe_url = f"http://{host}:{port}/docs"

    try:
        requests.get(probe_url, timeout=1)
        return 
    except requests.exceptions.RequestException:
        pass

    print(f"Starting {label} on {host}:{port} ({module_path})...")

    subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", module_path,
            "--host", host, "--port", str(port),
        ]
    )

    for _ in range(15):
        try:
            requests.get(probe_url, timeout=1)
            print(f"{label} started")
            return
        except requests.exceptions.RequestException:
            time.sleep(1)

    print(f"WARNING: {label} did not respond after 15s — check module_path.")


def ensure_chatbot_site_running(script_path: str, host: str, port: int) -> bool:
    
    probe_url = f"http://{host}:{port}"

    try:
        requests.get(probe_url, timeout=1)
        return True  
    except requests.exceptions.RequestException:
        pass

    if not os.path.isfile(script_path):
        print(f"ERROR: chatbot app script not found at: {script_path}")
        return False

    subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", script_path,
            "--server.port", str(port),
            "--server.headless", "true",
        ],
        cwd=os.path.dirname(script_path),
    )

    for _ in range(20):
        try:
            requests.get(probe_url, timeout=1)
            return True
        except requests.exceptions.RequestException:
            time.sleep(1)

    return False


if "backends_started" not in st.session_state:
    
    start_backend(
        module_path="backend.main:app",  
        host="127.0.0.1",
        port=8001,
        label="Projects/Tasks API",
    )
    
    st.session_state["backends_started"] = True

st.set_page_config(
    page_title="Annotation Platform Tracker",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

layout.apply_base_styles()

CHATBOT_URL = f"http://localhost:{CHATBOT_APP_PORT}"


def render_floating_chatbot() -> None:
    """
    Render the AI Assistant as a floating, draggable widget on top of the
    dashboard (instead of replacing the whole page like before).

    This mirrors the "floating card" look used in the chatbot's own
    application.py (dark #1F4E79 header bar, white rounded card, drop
    shadow), but keeps the dashboard visible underneath, and adds a
    small header drag-handle + close button so the panel can be moved
    around or dismissed without losing your place on the dashboard.
    """

    st.markdown(
        """
        <style>
        /* Floating widget "card" - pinned bottom-right by default */
        .st-key-floating_chat_panel {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 400px;
            max-width: 92vw;
            height: 700px;
            max-height: 90vh;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            z-index: 9999;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            padding: 0 !important;
        }

        /* Drag handle / title bar */
        .st-key-floating_chat_header {
            flex: 0 0 auto;
            background: #1F4E79;
            padding: 8px 6px 8px 16px;
            display: flex;
            align-items: center;
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
            user-select: none;
        }
        .st-key-floating_chat_header [data-testid="column"]:first-child p {
            color: #ffffff !important;
            font-weight: 600;
            font-size: 0.95rem;
            margin: 0 !important;
        }
        .st-key-floating_chat_header button {
            background: transparent !important;
            border: none !important;
            color: #ffffff !important;
            font-size: 14px !important;
            padding: 2px 8px !important;
        }
        .st-key-floating_chat_header button:hover {
            background: rgba(255, 255, 255, 0.15) !important;
        }

        /* Iframe body fills the rest of the card */
        .st-key-floating_chat_body {
            flex: 1 1 auto;
            display: flex;
        }
        .st-key-floating_chat_body iframe {
            border: none;
            width: 100%;
            height: 100%;
            flex: 1 1 auto;
        }

        /* Small circular "reopen" toggle button */
        .st-key-floating_chat_toggle {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 9998;
        }
        .st-key-floating_chat_toggle button {
            width: 56px !important;
            height: 56px !important;
            border-radius: 50% !important;
            font-size: 22px !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.28);
            background: #1F4E79 !important;
            color: white !important;
            border: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="floating_chat_panel"):
        with st.container(key="floating_chat_header"):
            head_col, close_col = st.columns([6, 1])
            with head_col:
                st.markdown("🤖 AI Annotation Assistant")
            with close_col:
                if st.button("✖", key="floating_chat_close", help="Close"):
                    st.session_state["show_chatbot"] = False
                    st.rerun()

        with st.container(key="floating_chat_body"):
            components.iframe(f"{CHATBOT_URL}/?embedded=1", height=640, scrolling=True)

    
    components.html(
        """
        <script>
        (function () {
            function init() {
                const doc = window.parent.document;
                const panel = doc.querySelector('.st-key-floating_chat_panel');
                const handle = doc.querySelector('.st-key-floating_chat_header');
                if (!panel || !handle) { setTimeout(init, 200); return; }
                if (handle.dataset.dragBound === '1') return;
                handle.dataset.dragBound = '1';

                try {
                    const saved = window.parent.localStorage.getItem('chatWidgetPos');
                    if (saved) {
                        const pos = JSON.parse(saved);
                        panel.style.left = pos.left;
                        panel.style.top = pos.top;
                        panel.style.right = 'auto';
                        panel.style.bottom = 'auto';
                    }
                } catch (e) {}

                let dragging = false, offsetX = 0, offsetY = 0;
                handle.style.cursor = 'move';

                handle.addEventListener('mousedown', function (e) {
                    if (e.target.closest('button')) return;
                    dragging = true;
                    const rect = panel.getBoundingClientRect();
                    offsetX = e.clientX - rect.left;
                    offsetY = e.clientY - rect.top;
                    e.preventDefault();
                });

                doc.addEventListener('mousemove', function (e) {
                    if (!dragging) return;
                    let left = e.clientX - offsetX;
                    let top = e.clientY - offsetY;
                    left = Math.max(0, Math.min(left, window.parent.innerWidth - panel.offsetWidth));
                    top = Math.max(0, Math.min(top, window.parent.innerHeight - panel.offsetHeight));
                    panel.style.left = left + 'px';
                    panel.style.top = top + 'px';
                    panel.style.right = 'auto';
                    panel.style.bottom = 'auto';
                });

                doc.addEventListener('mouseup', function () {
                    if (!dragging) return;
                    dragging = false;
                    try {
                        window.parent.localStorage.setItem('chatWidgetPos', JSON.stringify({
                            left: panel.style.left,
                            top: panel.style.top
                        }));
                    } catch (e) {}
                });
            }
            init();
        })();
        </script>
        """,
        height=0,
    )


def render_floating_toggle() -> None:
    """Small circular button to reopen the widget after it's been closed,
    without needing to reconnect to Label Studio again."""
    with st.container(key="floating_chat_toggle"):
        if st.button("🤖", key="floating_chat_reopen", help="Open AI Assistant"):
            st.session_state["show_chatbot"] = True
            st.rerun()


st.markdown("""
    <style>
    /* The chevron icon relies on the Material Symbols font, which may not
       load in this environment (offline/blocked CDN) - in that case it
       renders as literal text ("expand_more"/"expand_less") on top of the
       button label. Rather than depend on a font that might not be
       available, hide that icon entirely inside the popover trigger and
       use a plain-text arrow in the label instead (see popover_label below). */
    div[data-testid="stPopover"] > div > button [data-testid="stIconMaterial"] {
        display: none !important;
    }

    /* Popover trigger button: keep label on one line, no overlap/wrapping */
    div[data-testid="stPopover"] > div > button {
        display: flex !important;
        align-items: center;
        justify-content: center;
        white-space: nowrap;
        overflow: hidden;
    }
    div[data-testid="stPopover"] > div > button p {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: inherit !important;
    }

    /* Fix hover contrast: force readable text color on hover */
    div[data-testid="stPopover"] > div > button:hover,
    div[data-testid="stPopover"] > div > button:focus {
        color: #F9FAFB !important;
        background-color: #1F2937 !important;
        border-color: #4B5563 !important;
    }
    div[data-testid="stPopover"] > div > button:hover p,
    div[data-testid="stPopover"] > div > button:focus p {
        color: #F9FAFB !important;
    }
    </style>
""", unsafe_allow_html=True)

mongodb = mongodb_url

_DEFAULTS: dict = {
    "projects": [],
    "selected_project": None,
    "tasks": [],
    "reviews_by_task": {},      
    "fetch_error": None,
    "api_url": "",
    "api_token": "",
    "task_page": 1,
    "task_status_filter": "All",
    "task_sort_col": "— none —",
    "visible_cols": DEFAULT_COLUMNS[:],   
    "_last_filter_sort": None,
    "chatbot_started": False,      
    "chatbot_launch_failed": False, 
    "show_chatbot": False,          
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if st.session_state.get("show_chatbot"):
    render_floating_chatbot()
elif st.session_state.get("chatbot_started"):
    render_floating_toggle()


st.markdown(layout.render_page_header(), unsafe_allow_html=True)

st.markdown("""
    <div style="
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 20px;
        background-color: #FFFFFF;
        color: #111827;
    ">
        <h3 style="margin:0 0 12px;font-size:1rem;font-weight:600;color:#111827;">
            How to Get Your Annotation Platform API Token
        </h3>
        <p style="margin:0 0 6px;color:#374151;font-size:0.875rem;">
            <strong>Step 1:</strong> Log in to your Annotation Platform account.
        </p>
        <p style="margin:0 0 6px;color:#374151;font-size:0.875rem;">
            <strong>Step 2:</strong> Click your avatar in the top-right corner and open
            <strong>Account &amp; Settings</strong>.
        </p>
        <p style="margin:0 0 14px;color:#374151;font-size:0.875rem;">
            <strong>Step 3:</strong> Locate the <strong>Access Token</strong> section and copy your token.
        </p>
        <div style="
            color: #92400E;
            padding: 10px 14px;
            border: 1px solid #FCD34D;
            border-radius: 6px;
            background: #FEF9C3;
            font-size: 0.8125rem;
        ">
            ⚠️ <strong>Keep your token private.</strong>
            Never share it publicly or commit it to source control.
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown(
    layout.render_section_header(
        title="Workspace Authentication",
        description="Enter your Annotation Platform URL and API token to retrieve available projects.",
    ),
    unsafe_allow_html=True,
)

col_url, col_token = st.columns([1, 1], gap="medium")

with col_url:
    api_url_input = st.text_input(
        label="Label Studio URL",
        value=st.session_state["api_url"],
        placeholder="https://app.humansignal.com",
        help="The base URL of your Label Studio instance - no trailing path.",
        key="input_url",
    )

with col_token:
    api_token_input = st.text_input(
        label="API Token",
        value=st.session_state["api_token"],
        placeholder="Paste your API token here…",
        type="password",
        help="Find this under Account & Settings → Access Token in Label Studio.",
        key="input_token",
    )

_, btn_col = st.columns([3, 1])
with btn_col:
    connect_clicked = st.button(
        "🔗 Connect & Load Projects",
        type="primary",
        use_container_width=True,
    )

if connect_clicked:
    raw_url = api_url_input.strip()
    raw_token = api_token_input.strip()

    if not raw_url or not raw_token:
        st.session_state["fetch_error"] = "Both the URL and API token are required."
    else:
        st.session_state["api_url"] = raw_url
        st.session_state["api_token"] = raw_token
        st.session_state["fetch_error"] = None

        with st.spinner("Connecting to Label Studio…"):
        
            response = requests.post(
                "http://localhost:8001/projects",
                json={
                    "api_url": raw_url,
                    "api_token": raw_token
                }
            )

            data = response.json()

            projects = data["projects"]
            error = data["error"]

        if error:
            st.session_state["fetch_error"] = error
            st.session_state["projects"] = []
            st.session_state["selected_project"] = None
            st.session_state["tasks"] = []
            st.session_state["reviews_by_task"] = {}
        else:
            st.session_state["projects"] = projects
            st.session_state["selected_project"] = None
            st.session_state["tasks"] = []
            st.session_state["reviews_by_task"] = {}
            st.session_state["task_page"] = 1

if st.session_state["fetch_error"]:
    st.markdown(layout.render_error_banner(st.session_state["fetch_error"]), unsafe_allow_html=True)

projects = st.session_state["projects"]

if projects and not st.session_state["fetch_error"]:
    n = len(projects)

    col1, col2 = st.columns([8,1])

    with col1:
        st.success(
            f"✅ Connected — {n} project{'s' if n != 1 else ''} found."
        )

    with col2:
        if st.button("🤖 Ask AI"):
            with st.spinner("Starting AI Assistant..."):
                started = ensure_chatbot_site_running(
                    script_path=CHATBOT_APP_FILE,
                    host="127.0.0.1",
                    port=CHATBOT_APP_PORT,
                )
            st.session_state["chatbot_started"] = started
            st.session_state["chatbot_launch_failed"] = not started
            if started:
                
                st.session_state["show_chatbot"] = True
            st.rerun()

    if st.session_state.get("chatbot_launch_failed"):
        st.error(
            f"Could not start the AI Assistant. Expected to find it at:\n\n"
            f"`{CHATBOT_APP_FILE}`\n\n"
            f"Check that application.py exists at that path, or update "
            f"CHATBOT_APP_FILE near the top of app.py."
        )
        st.session_state["chatbot_launch_failed"] = False

if st.session_state["api_url"]:
    st.markdown(
        layout.render_section_header(
            title="Available Projects",
            description="Select a project to view its details and tasks.",
        ),
        unsafe_allow_html=True,
    )

    if not projects:
        st.markdown(
            layout.render_empty_state(
                icon="🗂️",
                heading="No projects found",
                body="Your workspace appears to be empty. Create a project in Label Studio first.",
            ),
            unsafe_allow_html=True,
        )
    else:
        COLS_PER_ROW = 3

        for row_projects in [projects[i: i + COLS_PER_ROW] for i in range(0, len(projects), COLS_PER_ROW)]:
            cols = st.columns(COLS_PER_ROW, gap="medium")

            for col, project in zip(cols, row_projects):
                with col:
                    st.markdown(
                        layout.render_project_card(
                            title=project.get("title", "Untitled"),
                            task_count=project.get("task_number", 0),
                            annotated=project.get("num_tasks_with_annotations", 0),
                            created_at=(project.get("created_at") or "")[:10],
                            project_id=project.get("id", "—"),
                        ),
                        unsafe_allow_html=True,
                    )

                    is_selected = (
                        st.session_state["selected_project"] is not None
                        and st.session_state["selected_project"].get("id") == project.get("id")
                    )
                    btn_label = "✅ Selected" if is_selected else "Select"

                    if st.button(btn_label, key=f"select_{project['id']}"):
                        st.session_state["selected_project"] = project
                        st.session_state["task_page"] = 1
                        st.session_state["visible_cols"] = DEFAULT_COLUMNS[:]

                        with st.spinner(f"Loading tasks for \"{project.get('title', '')}\"…"):
                            response = requests.post(
                                "http://localhost:8001/tasks",
                                json={
                                    "api_url": st.session_state["api_url"],
                                    "api_token": st.session_state["api_token"],
                                    "project_id": project["id"]
                                }
                            )

                            tasks = response.json()["tasks"]
                            st.session_state["tasks"] = tasks

                        with st.spinner("Loading review data…"):
                            reviews_by_task = fetch_reviews(
                                api_url=st.session_state["api_url"],
                                api_token=st.session_state["api_token"],
                                project_id=project["id"],
                            )
                            st.session_state["reviews_by_task"] = reviews_by_task

                        
                        with st.spinner("Syncing to MongoDB…"):
                            df_sync = build_tasks_dataframe(
                                tasks,
                                reviews_by_task=reviews_by_task,
                                project_title=project.get("title", ""),
                            )
                            try:
                                store_mongodb(df_sync, mongodb, project.get("title", ""))
                            except Exception as sync_exc:
                                # Persistence failures shouldn't block viewing the data
                                st.session_state["fetch_error"] = None
                                st.warning(f"Could not sync to MongoDB: {sync_exc}")

                        st.rerun()

selected = st.session_state["selected_project"]

if selected:
    st.markdown(
        layout.render_section_header(
            title=f"Project Overview — {selected.get('title', '')}",
            description="Summary information for the selected project.",
        ),
        unsafe_allow_html=True,
    )

    total_tasks = selected.get("task_number", 0)
    annotated_tasks = selected.get("num_tasks_with_annotations", 0)
    pending_tasks = total_tasks - annotated_tasks
    completion_pct = f"{round(annotated_tasks / total_tasks * 100)}%" if total_tasks > 0 else "—"

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        st.markdown(layout.render_stat_card("Total Tasks", str(total_tasks), "in this project"), unsafe_allow_html=True)
    with c2:
        st.markdown(layout.render_stat_card("Annotated", str(annotated_tasks), "tasks completed"), unsafe_allow_html=True)
    with c3:
        st.markdown(layout.render_stat_card("Pending", str(pending_tasks), "awaiting annotation"), unsafe_allow_html=True)
    with c4:
        st.markdown(layout.render_stat_card("Completion", completion_pct, "of tasks annotated"), unsafe_allow_html=True)

if selected:
    st.markdown(
        layout.render_section_header(
            title="Project Tasks",
            description="View and manage task information associated with the selected project.",
        ),
        unsafe_allow_html=True,
    )

    tasks = st.session_state["tasks"]

    if not tasks:
        st.markdown(
            layout.render_empty_state(
                icon="📭",
                heading="No tasks found",
                body="This project has no tasks yet, or they could not be loaded.",
            ),
            unsafe_allow_html=True,
        )
    else:
        df_full = build_tasks_dataframe(
            tasks,
            reviews_by_task=st.session_state.get("reviews_by_task", {}),
            project_title=selected.get("title", ""),
        )

        filter_col, sort_col, col_picker_col = st.columns([1.5, 1.5, 2.2], gap="medium")

        with filter_col:
            status_options = ["All", "Completed", "Pending"]
            status_filter = st.selectbox(
                "Filter by status",
                options=status_options,
                index=status_options.index(st.session_state["task_status_filter"])
                if st.session_state["task_status_filter"] in status_options else 0,
                key="task_status_filter",
            )

        available_sort_cols = sorted(df_full.columns.tolist())
        sort_options = ["— none —"] + available_sort_cols

        with sort_col:
            sort_by = st.selectbox(
                "Sort by column",
                options=sort_options,
                index=sort_options.index(st.session_state["task_sort_col"])
                if st.session_state["task_sort_col"] in sort_options else 0,
                key="task_sort_col",
            )

        with col_picker_col:
            st.markdown(
                '<p style="font-size:0.75rem;color:#6B7280;margin:0 0 2px;'
                'font-family:Inter,Segoe UI,sans-serif;font-weight:500;">'
                'Visible columns</p>',
                unsafe_allow_html=True,
            )

            available_cols = [c for c in ALL_COLUMNS if c in df_full.columns]
            saved_visible = [c for c in st.session_state["visible_cols"] if c in available_cols]
            if not saved_visible:
                saved_visible = [c for c in DEFAULT_COLUMNS if c in available_cols]

            popover_label = f"Columns ({len(saved_visible)}) ▾"
            with st.popover(popover_label, use_container_width=True):
                st.markdown(
                    '<p style="font-size:0.8rem;color:#374151;font-weight:600;margin:0 0 8px;">'
                    'Select columns to display</p>',
                    unsafe_allow_html=True,
                )
                new_visible: list[str] = []
                for col_name in available_cols:
                    checked = st.checkbox(
                        col_name,
                        value=(col_name in saved_visible),
                        key=f"colchk_{col_name}",
                    )
                    if checked:
                        new_visible.append(col_name)

                pick_col1, pick_col2 = st.columns(2)
                with pick_col1:
                    if st.button("Select all", key="colchk_select_all", use_container_width=True):
                        for c in available_cols:
                            st.session_state[f"colchk_{c}"] = True
                        st.rerun()
                with pick_col2:
                    if st.button("Clear", key="colchk_clear", use_container_width=True):
                        for c in available_cols:
                            st.session_state[f"colchk_{c}"] = False
                        st.rerun()

            visible_cols = new_visible if new_visible else saved_visible
            st.session_state["visible_cols"] = visible_cols

        df_display = df_full.copy()
        if status_filter != "All":
            df_display = df_display[
                df_display["Status"].astype(str).str.strip().str.capitalize() == status_filter
            ]

        if sort_by != "— none —" and sort_by in df_display.columns:
            df_display = df_display.sort_values(by=sort_by, ascending=True).reset_index(drop=True)

        safe_cols = [c for c in st.session_state["visible_cols"] if c in df_display.columns]
        df_display_visible = df_display[safe_cols] if safe_cols else df_display

        current_key = (status_filter, sort_by, tuple(safe_cols))
        if st.session_state.get("_last_filter_sort") != current_key:
            st.session_state["task_page"] = 1
            st.session_state["_last_filter_sort"] = current_key

        PAGE_SIZE = 10
        total_rows = len(df_display_visible)
        total_pages = max(1, -(-total_rows // PAGE_SIZE))   # ceiling division
        page = max(1, min(st.session_state["task_page"], total_pages))
        st.session_state["task_page"] = page

        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        df_page = df_display_visible.iloc[start:end]

        st.caption(
            f"Showing rows {start + 1}–{min(end, total_rows)} of {total_rows}  "
            f"·  {len(safe_cols)} column(s) visible  "
            f"·  page {page} of {total_pages}"
        )

        _COLUMN_CONFIG = {
            "Task ID": st.column_config.TextColumn("Task ID", width="small"),
            "Project": st.column_config.TextColumn("Project", width="medium"),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Owner": st.column_config.TextColumn("Owner", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Annotator": st.column_config.TextColumn("Annotator", width="medium"),
            "Annotation IDs": st.column_config.TextColumn("Annotation IDs", width="medium"),
            "Annotation Count": st.column_config.NumberColumn("Annotation Count", width="small"),
            "Reviewed": st.column_config.TextColumn("Reviewed", width="small"),
            "Reviewer": st.column_config.TextColumn("Reviewer", width="medium"),
            "Review Status": st.column_config.TextColumn("Review Status", width="small"),
            "Lead Time (s)": st.column_config.NumberColumn("Lead Time (s)", width="small", format="%.2f"),
            "Created": st.column_config.TextColumn("Created", width="small"),
            "Updated": st.column_config.TextColumn("Updated", width="small"),
            "Completed At": st.column_config.TextColumn("Completed At", width="small"),
            
        }
        active_col_config = {k: v for k, v in _COLUMN_CONFIG.items() if k in safe_cols}

        st.dataframe(
            df_page,
            use_container_width=True,
            hide_index=True,
            height=min(460, 56 + len(df_page) * 35),
            column_config=active_col_config,
        )

        prev_col, page_info_col, next_col = st.columns([1, 3, 1])

        with prev_col:
            if st.button("◀ Prev", disabled=(page <= 1), key="page_prev"):
                st.session_state["task_page"] -= 1
                st.rerun()

        with page_info_col:
            st.markdown(
                f"<div style='text-align:center;padding-top:6px;font-size:0.875rem;"
                f"color:#374151;'>Page <strong>{page}</strong> of "
                f"<strong>{total_pages}</strong></div>",
                unsafe_allow_html=True,
            )

        with next_col:
            if st.button("Next ▶", disabled=(page >= total_pages), key="page_next"):
                st.session_state["task_page"] += 1
                st.rerun()

        csv_data = df_display_visible.to_csv(index=False).encode("utf-8")
        safe_name = selected.get("title", "tasks").replace(" ", "_").replace("/", "-")
        st.download_button(
            label="⬇️ Download filtered view as CSV",
            data=csv_data,
            file_name=f"{safe_name}_tasks.csv",
            mime="text/csv",
            key="csv_export",
        )