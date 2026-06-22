import streamlit as st


import src.base_layout as layout
from data.retrieve_task import fetch_projects, fetch_tasks, build_tasks_dataframe,store_mongodb,fetch_mongo
from data.api import mongodb_url



st.set_page_config(
    page_title="Label Studio Dashboard",
    page_icon="🏷️",
    layout="wide",      
    initial_sidebar_state="collapsed",
)


layout.apply_base_styles()

mongodb = mongodb_url()
if "projects" not in st.session_state:
    st.session_state["projects"] = []   

if "selected_project" not in st.session_state:
    st.session_state["selected_project"] = None    

if "tasks" not in st.session_state:
    st.session_state["tasks"]  = []     

if "fetch_error" not in st.session_state:
    st.session_state["fetch_error"]  = None    

if "api_url" not in st.session_state:
    st.session_state["api_url"]  = ""

if "api_token" not in st.session_state:
    st.session_state["api_token"] = ""


st.markdown(layout.render_page_header(), unsafe_allow_html=True)


st.markdown("""
            <div style="order:1px solid #d1d5db;color:black; border-radius:10px; padding:20px; margin-bottom:20px; background-color:white;">
            <h3>How to Get Your Label Studio API Token</h3>
            <p><strong>Step 1:</strong> Log in to your Label Studio account.</p>
            <p><strong>Step 2:</strong> Click your profile/avatar in the top-right corner and open
            <strong>Account & Settings</strong>.</p>
            <p><strong>Step 3:</strong> Locate the <strong>Access Token</strong> section and copy your token.</p>
            
            <div style="color:black;margin-top:15px;padding:10px;border:1px solid #facc15;border-radius:6px;background:#fef9c3;">

             <strong>Keep your token private.</strong>
            Never share it publicly or commit it to source control.
            </div>
            </div>
            
            """, unsafe_allow_html=True)

st.markdown(
    layout.render_section_header(
        title="Workspace Authentication",
        description="Enter your Label Studio API token to retrieve available projects.",
    ),
    unsafe_allow_html=True,
)


col_url, col_token = st.columns([1, 1], gap="medium")

with col_url:
   
    api_url_input = st.text_input(
        label="Label Studio URL",
        value=st.session_state["api_url"],
        placeholder="https://app.humansignal.com",
        help="The base URL of your Label Studio instance.",
        key="input_url",
    )

with col_token:
    api_token_input = st.text_input(
        label="API Token",
        value=st.session_state["api_token"],
        placeholder="Enter your API token…",
        type="password",    
        help="Find this under Account & Settings → Access Token in Label Studio.",
        key="input_token",
    )


_, btn_col = st.columns([3, 1])   
with btn_col:
    connect_clicked = st.button("🔗 Connect & Load Projects", type="primary", use_container_width=True)


if connect_clicked:
   
    if not api_url_input.strip() or not api_token_input.strip():
        st.session_state["fetch_error"] = "Both the URL and API token are required."
    else:
        st.session_state["api_url"] = api_url_input.strip()
        st.session_state["api_token"] = api_token_input.strip()
        st.session_state["fetch_error"] = None

        with st.spinner("Connecting to Label Studio…"):
            projects, error = fetch_projects(
                api_url=st.session_state["api_url"],
                api_token=st.session_state["api_token"],
            )

        if error:
            st.session_state["fetch_error"] = error
            st.session_state["projects"] = []
        else:
            st.session_state["projects"] = projects
            st.session_state["selected_project"] = None
            st.session_state["tasks"] = []
            

if st.session_state["fetch_error"]:
    st.markdown(
        layout.render_error_banner(st.session_state["fetch_error"]),
        unsafe_allow_html=True,
    )

if st.session_state["projects"] and not st.session_state["fetch_error"]:
    count = len(st.session_state["projects"])
    st.success(f"✅ Connected — {count} project{'s' if count != 1 else ''} found.")


projects = st.session_state["projects"]

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

        
        rows = [
            projects[i : i + COLS_PER_ROW]
            for i in range(0, len(projects), COLS_PER_ROW)
        ]

        for row in rows:
            cols = st.columns(COLS_PER_ROW, gap="medium")

            for col, project in zip(cols, row):
                with col:
                    st.markdown(
                        layout.render_project_card(
                            title=project.get("title", "Untitled"),
                            task_count=project.get("task_number", 0),
                            annotated=project.get("num_tasks_with_annotations", 0),
                            created_at=project.get("created_at", "")[:10],
                            project_id=project.get("id", "—"),
                        ),
                        unsafe_allow_html=True,
                    )

                    btn_label = (
                        "✅ Selected"
                        if st.session_state["selected_project"] == project
                        else "Select"
                    )
                    if st.button(btn_label, key=f"select_{project['id']}"):
                        st.session_state["selected_project"] = project
                        
                        with st.spinner(f"Loading tasks for \"{project.get('title', '')}\"…"):
                            st.session_state["tasks"] = fetch_tasks(
                                api_url=st.session_state["api_url"],
                                api_token=st.session_state["api_token"],
                                project_id=project["id"],
                            )
                        st.rerun()   #



selected = st.session_state["selected_project"]

if selected:
    store_mongodb(
        st.session_state["api_url"],
        st.session_state["api_token"],
        mongodb,
        selected.get("title", ""),
        selected.get("id", ""),
    )
print(selected)

if selected:
    st.markdown(
        layout.render_section_header(
            title=f"Project Overview — {selected.get('title', '')}",
            description="Summary information for the selected project.",
        ),
        unsafe_allow_html=True,
    )


    total_tasks      = selected.get("task_number", 0)
    annotated_tasks  = selected.get("num_tasks_with_annotations", 0)
    pending_tasks    = total_tasks - annotated_tasks
    
    completion_pct   = (
        f"{round(annotated_tasks / total_tasks * 100)}%"
        if total_tasks > 0
        else "—"
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        st.markdown(
            layout.render_stat_card(
                label="Total Tasks",
                value=str(total_tasks),
                sub="in this project",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            layout.render_stat_card(
                label="Annotated",
                value=str(annotated_tasks),
                sub="tasks completed",
            ),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            layout.render_stat_card(
                label="Pending",
                value=str(pending_tasks),
                sub="awaiting annotation",
            ),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            layout.render_stat_card(
                label="Completion",
                value=completion_pct,
                sub="of tasks annotated",
            ),
            unsafe_allow_html=True,
        )


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
        
        df = fetch_mongo(project_title=selected.get("title", ""))

        # ── column names coming from MongoDB 
        # task_id | project_name | owner | annotator | completed_at | status | updated
        STATUS_COL = "status"   

   
        filter_col, sort_col, spacer = st.columns([2, 2, 1])

        with filter_col:
            status_filter = st.selectbox(
                "Filter by status",
                options=["All", "Completed", "Pending"],
                index=0,
                key="task_status_filter",
            )

       
        all_columns = sorted(df.columns.tolist())
        with sort_col:
            sort_by = st.selectbox(
                "Sort by column",
                options=["— none —"] + all_columns,
                index=0,
                key="task_sort_col",
            )

       
        if status_filter != "All":
            
            df_display = df[df[STATUS_COL].str.strip().str.capitalize() == status_filter]
        else:
            df_display = df.copy()

       
        if sort_by != "— none —":
            df_display = df_display.sort_values(by=sort_by, ascending=True).reset_index(drop=True)

      
        PAGE_SIZE   = 10
        total_rows  = len(df_display)
        total_pages = max(1, -(-total_rows // PAGE_SIZE))   # ceiling division

        if "task_page" not in st.session_state:
            st.session_state["task_page"] = 1

        # Reset to page 1 whenever filter/sort changes
        filter_sort_key = (status_filter, sort_by)
        if st.session_state.get("_last_filter_sort") != filter_sort_key:
            st.session_state["task_page"] = 1
            st.session_state["_last_filter_sort"] = filter_sort_key

        page = st.session_state["task_page"]
        start = (page - 1) * PAGE_SIZE
        end   = start + PAGE_SIZE
        df_page = df_display.iloc[start:end]

        # Caption
        st.caption(
            f"Showing {start + 1}–{min(end, total_rows)} of {total_rows} task(s)  "
            f"(page {page} of {total_pages})"
        )

        # Table
        st.dataframe(
            df_page,
            use_container_width=True,
            hide_index=True,
            column_config={
                "task_id":      st.column_config.TextColumn("Task ID",      width="small"),
                "project_name": st.column_config.TextColumn("Project",      width="medium"),
                "status":       st.column_config.TextColumn("Status",       width="small"),
                "owner":        st.column_config.TextColumn("Owner",        width="medium"),
                "annotator":    st.column_config.TextColumn("Annotator",    width="medium"),
                "completed_at": st.column_config.TextColumn("Completed At", width="small"),
                "updated":      st.column_config.TextColumn("Updated",      width="small"),
            },
        )


        prev_col, page_info_col, next_col = st.columns([1, 3, 1])
        with prev_col:
            if st.button("◀ Prev", disabled=(page <= 1), key="page_prev"):
                st.session_state["task_page"] -= 1
                st.rerun()
        with page_info_col:
            st.markdown(
                f"<div style='text-align:center; padding-top:6px;'>Page <strong>{page}</strong> of <strong>{total_pages}</strong></div>",
                unsafe_allow_html=True,
            )
        with next_col:
            if st.button("Next ▶", disabled=(page >= total_pages), key="page_next"):
                st.session_state["task_page"] += 1
                st.rerun()


        csv_data = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download as CSV",
            data=csv_data,
            file_name=f"{selected.get('title', 'tasks').replace(' ', '_')}_tasks.csv",
            mime="text/csv",
        )

        
