from __future__ import annotations
import logging
from collections import defaultdict
from typing import Any
import os
import pandas as pd
from label_studio_sdk import LabelStudio
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv



load_dotenv()
mongodb_url = os.getenv("MONGODB_TOKEN")

logger = logging.getLogger(__name__)

MAX_TASKS = 1000
MAX_REVIEWS = 2000



ALL_COLUMNS: list[str] = [
    "Task ID",           
    "Title",             
    "Owner",             
    "Status",            
    "Annotator",         
    "Annotation IDs",    
    "Annotation Count",  
    "Completed At",      
    "Reviewed",          
    "Reviewer",          
    "Review Status",     
    "Lead Time (s)",     
    "Created",           
    "Updated",           
    "Project",           
]

DEFAULT_COLUMNS: list[str] = [
    "Task ID",
    "Title",
    "Owner",
    "Status",
    "Annotator",
    "Annotation IDs",
    "Completed At",
    "Reviewed",
    "Reviewer",
    "Review Status",
    "Updated",
]



def make_client(api_url: str, api_token: str) -> LabelStudio:
    """Return an authenticated Label Studio SDK client."""
    return LabelStudio(base_url=api_url.strip().rstrip("/"), api_key=api_token.strip())



def _resolve_email(user_ref: Any, fallback: str = "-") -> str:
    
    if user_ref is None:
        return fallback
    email = getattr(user_ref, "email", None)
    if email:
        return str(email)
    if isinstance(user_ref, dict):
        return (
            user_ref.get("email")
            or user_ref.get("username")
            or (f"user#{user_ref['id']}" if "id" in user_ref else fallback)
        )
    if isinstance(user_ref, int):
        return f"user#{user_ref}"
    return fallback


def _extract_title(task_data: Any, fallback: str) -> str:
    
    if not isinstance(task_data, dict):
        return fallback
    for key in ("text", "title", "content", "caption", "value"):
        if key in task_data:
            return str(task_data[key])[:80]
    for key in ("image", "audio", "url"):
        if key in task_data:
            raw = str(task_data[key])
            if len(raw) <= 80:
                return raw
    if task_data:
        first_key = next(iter(task_data))
        return f"{first_key}: {str(task_data[first_key])[:60]}"
    return fallback


def _sdk_task_to_dict(task: Any) -> dict:
    
    raw: dict = {}
    try:
        raw = task.model_dump() or {}
    except Exception:
        try:
            raw = vars(task) or {}
        except Exception:
            pass

    annotations_raw = getattr(task, "annotations", None) or raw.get("annotations") or []
    annotations_list: list[dict] = []
    for ann in annotations_raw:
        ann_dict: dict = {}
        try:
            ann_dict = ann.model_dump() or {}
        except Exception:
            try:
                ann_dict = vars(ann) or {}
            except Exception:
                ann_dict = ann if isinstance(ann, dict) else {}

        annotations_list.append({
            "id": ann_dict.get("id") or getattr(ann, "id", None),
            "completed_by": ann_dict.get("completed_by") or getattr(ann, "completed_by", None),
            "lead_time": ann_dict.get("lead_time") or getattr(ann, "lead_time", None),
            "was_cancelled": ann_dict.get("was_cancelled", False) or getattr(ann, "was_cancelled", False),
            "created_at": str(ann_dict.get("created_at") or getattr(ann, "created_at", "") or ""),
            "reviews": ann_dict.get("reviews") or [],
        })

    created_by = raw.get("created_by") or getattr(task, "created_by", None)
    owner_email = _resolve_email(created_by)
    if owner_email == "-":
        owner_email = (
            getattr(task, "created_username", None)
            or raw.get("created_username")
            or "-"
        )

    return {
        "id": task.id,
        "data": dict(raw.get("data") or getattr(task, "data", {}) or {}),
        "is_labeled": bool(raw.get("is_labeled", False) or getattr(task, "is_labeled", False)),
        "state": raw.get("state") or getattr(task, "state", None),
        "owner": str(owner_email),
        "annotations": annotations_list,
        "created_at": str(raw.get("created_at") or getattr(task, "created_at", "") or ""),
        "updated_at": str(raw.get("updated_at") or getattr(task, "updated_at", "") or ""),
    }


def _parse_annotations(annotations: list[dict], task_reviews: list[dict]) -> dict[str, Any]:
    
    if not annotations:
        return {
            "annotator": "-",
            "annotation_ids": "-",
            "annotation_count": 0,
            "completed_at": "-",
            "reviewed": "No",
            "reviewer": "-",
            "review_status": "-",
            "lead_time": 0.0,
        }

    annotators: list[str] = []
    ann_ids: list[str] = []
    lead_times: list[float] = []
    completed_ats: list[str] = []

    for ann in annotations:
        if ann.get("was_cancelled"):
            continue

        ann_id = ann.get("id")
        if ann_id is not None:
            ann_ids.append(str(ann_id))

        annotators.append(_resolve_email(ann.get("completed_by")))

        lt = ann.get("lead_time")
        if isinstance(lt, (int, float)) and lt > 0:
            lead_times.append(float(lt))

        ca = str(ann.get("created_at") or "")
        if ca:
            completed_ats.append(ca[:10])

    embedded_reviews: list[dict] = []
    for ann in annotations:
        embedded_reviews.extend(ann.get("reviews") or [])

    all_reviews = task_reviews if task_reviews else embedded_reviews

    reviewers: list[str] = []
    review_result: str = "-"

    if all_reviews:
        sorted_reviews = sorted(
            all_reviews,
            key=lambda rv: rv.get("updated_at") or rv.get("created_at") or "",
            reverse=True,
        )
        for rv in sorted_reviews:
            rv_user = rv.get("created_by") or rv.get("reviewed_by")
            reviewers.append(_resolve_email(rv_user))

        latest = sorted_reviews[0].get("result", "") or ""
        review_result = latest.capitalize() if latest else "-"

    avg_lead = round(sum(lead_times) / len(lead_times), 2) if lead_times else 0.0

    return {
        "annotator": ", ".join(dict.fromkeys(a for a in annotators if a != "-")) or "-",
        "annotation_ids": ", ".join(ann_ids) or "-",
        "annotation_count": len(ann_ids),
        "completed_at": min(completed_ats) if completed_ats else "-",
        "reviewed": "Yes" if all_reviews else "No",
        "reviewer": ", ".join(dict.fromkeys(r for r in reviewers if r != "-")) or "-",
        "review_status": review_result,
        "lead_time": avg_lead,
    }


def _classify_error(exc: Exception, api_url: str) -> str:
    
    msg = str(exc)
    exc_type = type(exc).__name__

    if "401" in msg or "Unauthorized" in msg:
        return (
            "API token rejected (HTTP 401). "
            "Copy the token from Account & Settings -> Access Token and "
            "ensure there are no leading/trailing spaces."
        )
    if "403" in msg or "Forbidden" in msg:
        return "Access denied (HTTP 403). Your token may lack the required permissions."
    if "404" in msg:
        return f"API endpoint not found at '{api_url}'. Verify the base URL."
    if "ConnectionError" in exc_type or "Connection" in msg:
        return f"Could not reach '{api_url}'. Check the URL and your network connection."
    if "Timeout" in exc_type or "timed out" in msg.lower():
        return "Request timed out. Label Studio may be slow or unreachable."
    if "SSLError" in exc_type or "SSL" in msg:
        return "SSL certificate error. Verify your instance's SSL configuration."
    return f"Unexpected error: {msg}"


def fetch_projects(api_url: str, api_token: str) -> tuple[list[dict], str | None]:
    """Retrieve all projects from a Label Studio workspace via the SDK."""
    if not api_url or not api_token:
        return [], "Both the Label Studio URL and API token are required."

    try:
        logger.info("fetch_projects: connecting to %s", api_url)
        client = make_client(api_url, api_token)
        raw_projects = list(client.projects.list())

        projects: list[dict] = []
        for p in raw_projects:
            projects.append({
                "id": p.id,
                "title": p.title or "Untitled",
                "task_number": getattr(p, "task_number", 0) or 0,
                "num_tasks_with_annotations": getattr(p, "num_tasks_with_annotations", 0) or 0,
                "created_at": str(getattr(p, "created_at", "") or ""),
                "updated_at": str(getattr(p, "updated_at", "") or ""),
                "label_config": getattr(p, "label_config", "") or "",
                "label_config_title": getattr(p, "label_config_title", "") or "",
            })

        logger.info("fetch_projects: retrieved %d projects", len(projects))
        return projects, None

    except Exception as exc:
        logger.exception("fetch_projects: error")
        return [], _classify_error(exc, api_url)



def fetch_tasks(api_url: str, api_token: str, project_id: int | str) -> list[dict]:
    """Retrieve all tasks for a project via the SDK. Returns [] on any error."""
    if not api_url or not api_token or not project_id:
        return []

    try:
        logger.info("fetch_tasks: fetching tasks for project %s", project_id)
        client = make_client(api_url, api_token)
        raw_tasks = list(client.tasks.list(project=int(project_id)))
        result = [_sdk_task_to_dict(t) for t in raw_tasks]
        logger.info("fetch_tasks: retrieved %d tasks", len(result))
        return result

    except Exception:
        logger.exception("fetch_tasks: error for project %s", project_id)
        return []



def fetch_reviews(api_url: str, api_token: str, project_id: int | str) -> dict[int, list[dict]]:
    
    if not api_url or not api_token or not project_id:
        return {}

    try:
        logger.info("fetch_reviews: fetching reviews for project %s", project_id)
        client = make_client(api_url, api_token)

        raw_reviews: list[Any] = []
        try:
            raw_reviews = list(client.reviews.list(project=int(project_id)))
        except AttributeError:
            import requests as _requests
            base = api_url.strip().rstrip("/")
            resp = _requests.get(
                f"{base}/api/reviews/",
                headers={"Authorization": f"Token {api_token.strip()}"},
                params={"project": project_id, "page_size": MAX_REVIEWS},
                timeout=20,
            )
            if resp.status_code == 404:
                logger.debug("fetch_reviews: reviews not available (Community edition)")
                return {}
            resp.raise_for_status()
            data = resp.json()
            raw_reviews = data.get("results", data) if isinstance(data, dict) else data

        by_task: dict[int, list[dict]] = defaultdict(list)
        for rv in raw_reviews:
            rv_dict: dict = {}
            try:
                rv_dict = rv.model_dump() or {}
            except Exception:
                rv_dict = rv if isinstance(rv, dict) else {}

            task_id = rv_dict.get("task") or getattr(rv, "task", None)
            if task_id is None:
                continue

            by_task[int(task_id)].append({
                "id": rv_dict.get("id") or getattr(rv, "id", None),
                "task": int(task_id),
                "annotation": rv_dict.get("annotation") or getattr(rv, "annotation", None),
                "result": rv_dict.get("result") or getattr(rv, "result", ""),
                "created_by": rv_dict.get("created_by") or getattr(rv, "created_by", None),
                "reviewed_by": rv_dict.get("reviewed_by") or getattr(rv, "reviewed_by", None),
                "created_at": str(rv_dict.get("created_at") or getattr(rv, "created_at", "") or ""),
                "updated_at": str(rv_dict.get("updated_at") or getattr(rv, "updated_at", "") or ""),
            })

        logger.info("fetch_reviews: indexed reviews for %d tasks", len(by_task))
        return dict(by_task)

    except Exception as exc:
        msg = str(exc)
        if "404" in msg:
            logger.debug("fetch_reviews: reviews endpoint not available (Community edition)")
        else:
            logger.warning("fetch_reviews: could not fetch reviews - %s", msg)
        return {}


def build_tasks_dataframe(
    tasks: list[dict],
    reviews_by_task: dict[int, list[dict]] | None = None,
    project_title: str = "",
) -> pd.DataFrame:
   
    reviews_by_task = reviews_by_task or {}
    rows: list[dict] = []

    for i, t in enumerate(tasks):
        task_id = t.get("id", i)
        annotations = t.get("annotations") or []
        task_reviews = reviews_by_task.get(int(task_id), [])
        ann_info = _parse_annotations(annotations, task_reviews)

        rows.append({
            "Task ID": f"#{task_id:06d}",
            "Project": project_title or "-",
            "Title": _extract_title(t.get("data") or {}, fallback=f"Task {i + 1}"),
            "Owner": t.get("owner") or "-",
            "Status": "Completed" if t.get("is_labeled") else "Pending",
            "Annotator": ann_info["annotator"],
            "Annotation IDs": ann_info["annotation_ids"],
            "Annotation Count": ann_info["annotation_count"],
            "Completed At": ann_info["completed_at"],
            "Reviewed": ann_info["reviewed"],
            "Reviewer": ann_info["reviewer"],
            "Review Status": ann_info["review_status"],
            "Lead Time (s)": ann_info["lead_time"],
            "Created": (t.get("created_at") or "")[:10],
            "Updated": (t.get("updated_at") or "")[:10],
            
        })

    if rows:
        return pd.DataFrame(rows, columns=ALL_COLUMNS)
    return pd.DataFrame(columns=ALL_COLUMNS)


def build_projects_dataframe(projects: list[dict]) -> pd.DataFrame:
    
    return pd.DataFrame([
        {
            "Project ID": p.get("id"),
            "Project Name": p.get("title", ""),
            "Task Count": p.get("task_number", 0),
            "Annotated Tasks": p.get("num_tasks_with_annotations", 0),
            "Created At": (p.get("created_at") or "")[:10],
            "Label Config Title": p.get("label_config_title", ""),
        }
        for p in projects
    ])



def store_mongodb(df: pd.DataFrame, mongo_url: str, project_title: str) -> None:
    
    if df is None or df.empty:
        logger.warning("store_mongodb: empty DataFrame for '%s' - nothing stored", project_title)
        return
    if not project_title:
        logger.error("store_mongodb: project_title is required")
        return
    if not mongo_url:
        logger.error("store_mongodb: mongo_url is required")
        return

    logger.info("store_mongodb: syncing %d rows for project '%s'", len(df), project_title)

    client_mongo = MongoClient(mongo_url)
    collection = client_mongo["All_selected_projects"][project_title]

    docs = df.to_dict(orient="records")
    operations = [
        UpdateOne({"Task ID": doc["Task ID"]}, {"$set": doc}, upsert=True)
        for doc in docs
        if doc.get("Task ID")
    ]
    if not operations:
        logger.warning("store_mongodb: no valid documents to upsert for '%s'", project_title)
        return

    result = collection.bulk_write(operations)
    logger.info(
        "store_mongodb: done - inserted=%d, modified=%d, matched=%d",
        result.upserted_count,
        result.modified_count,
        result.matched_count,
    )


def fetch_mongo(project_title: str) -> pd.DataFrame:
   
    logger.info("fetch_mongo: reading collection '%s'", project_title)
    try:
        client = MongoClient(mongodb_url)
        collection = client["All_selected_projects"][project_title]
        documents = list(collection.find({}, {"_id": 0}))
        logger.info("fetch_mongo: retrieved %d documents", len(documents))
        if not documents:
            return pd.DataFrame(columns=ALL_COLUMNS)
        df = pd.DataFrame(documents)
        # Guarantee every ALL_COLUMNS field exists, in canonical order
        for col in ALL_COLUMNS:
            if col not in df.columns:
                df[col] = "-"
        return df[ALL_COLUMNS]
    except Exception:
        logger.exception("fetch_mongo: error reading from MongoDB")
        return pd.DataFrame(columns=ALL_COLUMNS)