from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from label_studio_sdk import LabelStudio
from pymongo import MongoClient
from data.api import mongodb_url
import json


logger = logging.getLogger(__name__)


def data_retrieval(api_url: str, api_token: str) -> pd.DataFrame:
    logger.info("data_retrieval: connecting to Label Studio at %s", api_url)
    client   = LabelStudio(base_url=api_url, api_key=api_token)
    projects = client.projects.list()

    rows = []
    for project in projects:
        logger.debug("data_retrieval: fetching tasks for project %s (%s)", project.id, project.title)
        tasks = client.tasks.list(project=project.id)
        for task in tasks:
            annotation_count = len(task.annotations) if task.annotations else 0
            rows.append({
                "Project ID":   project.id,
                "Project Name": project.title,
                "Task ID":      task.id,
                "Status":       task.state,
                "Annotations":  annotation_count,
            })

    logger.info("data_retrieval: collected %d task rows across all projects", len(rows))
    return pd.DataFrame(rows)


def make_client(api_url: str, api_token: str) -> LabelStudio:
    return LabelStudio(base_url=api_url.rstrip("/"), api_key=api_token)


def fetch_projects(api_url: str, api_token: str) -> tuple[list[dict], str | None]:
    if not api_url or not api_token:
        logger.warning("fetch_projects: missing api_url or api_token")
        return [], "Both the Label Studio URL and API token are required."

    try:
        logger.info("fetch_projects: connecting to %s", api_url)
        client       = make_client(api_url, api_token)
        raw_projects = client.projects.list()

        projects = []
        for p in raw_projects:
            projects.append({
                "id":                         p.id,
                "title":                      p.title or "Untitled",
                "task_number":                getattr(p, "task_number", 0) or 0,
                "num_tasks_with_annotations": getattr(p, "num_tasks_with_annotations", 0) or 0,
                "created_at":                 str(getattr(p, "created_at", "") or ""),
                "updated_at":                 str(getattr(p, "updated_at", "") or ""),
                "label_config":               getattr(p, "label_config", "") or "",
                "label_config_title":         getattr(p, "label_config_title", "") or "",
            })

        logger.info("fetch_projects: retrieved %d projects", len(projects))
        return projects, None

    except Exception as exc:
        error_msg = str(exc)
        if "401" in error_msg or "Unauthorized" in error_msg:
            logger.error("fetch_projects: authentication failed for %s", api_url)
            return [], "Invalid API token. Check your token under Account & Settings in Label Studio."
        if "403" in error_msg or "Forbidden" in error_msg:
            logger.error("fetch_projects: access denied for %s", api_url)
            return [], "Access denied. Your token may not have the required permissions."
        if "404" in error_msg:
            logger.error("fetch_projects: API not found at %s", api_url)
            return [], f"API not found at '{api_url}'. Double-check the base URL."
        if "ConnectionError" in type(exc).__name__ or "Connection" in error_msg:
            logger.error("fetch_projects: could not reach %s", api_url)
            return [], f"Could not reach '{api_url}'. Check the URL and your network connection."
        if "Timeout" in type(exc).__name__:
            logger.error("fetch_projects: request timed out for %s", api_url)
            return [], "Request timed out. Label Studio may be slow or unreachable."
        logger.exception("fetch_projects: unexpected error")
        return [], f"Unexpected error: {error_msg}"


def fetch_tasks(api_url: str, api_token: str, project_id: int | str) -> list[dict]:
    if not api_url or not api_token or not project_id:
        logger.warning("fetch_tasks: missing required arguments (api_url, api_token, or project_id)")
        return []

    try:
        logger.info("fetch_tasks: fetching tasks for project %s", project_id)
        client    = make_client(api_url, api_token)
        raw_tasks = client.tasks.list(project=project_id)

        tasks = []
        for t in raw_tasks:
            task_data = {}
            if hasattr(t, "data") and t.data:
                try:
                    task_data = dict(t.data)
                except (TypeError, ValueError):
                    task_data = {"raw": str(t.data)}

            annotations_raw  = t.annotations if t.annotations else []
            annotations_list = []
            for ann in annotations_raw:
                completed_by = {}
                if hasattr(ann, "completed_by") and ann.completed_by:
                    cb = ann.completed_by
                    completed_by = {
                        "email": getattr(cb, "email", str(cb)),
                        "id":    getattr(cb, "id", None),
                    }
                annotations_list.append({
                    "id":           getattr(ann, "id", None),
                    "completed_by": completed_by,
                    "created_at":   str(getattr(ann, "created_at", "") or ""),
                })

            tasks.append({
                "id":          t.id,
                "state":       getattr(t, "state", None),
                "owner_name":  getattr(t, "created_username", None),
                "is_labeled":  bool(getattr(t, "is_labeled", False)),
                "annotations": annotations_list,
                "updated_at":  str(getattr(t, "updated_at", "") or ""),
            })

        logger.info("fetch_tasks: retrieved %d tasks for project %s", len(tasks), project_id)
        return tasks

    except Exception as exc:
        logger.exception("fetch_tasks: error fetching tasks for project %s", project_id)
        return []


def build_tasks_dataframe(tasks: list[dict], project_title: str = "") -> pd.DataFrame:
    rows = []
    for i, t in enumerate(tasks):
        task_data  = t.get("data", {})
        title_text = ""

        if isinstance(task_data, dict):
            for key in ("text", "title"):
                if key in task_data:
                    title_text = str(task_data[key])[:80]
                    break
            if not title_text and task_data:
                first_key  = next(iter(task_data))
                title_text = f"{first_key}: {str(task_data[first_key])[:60]}"

        title_text  = title_text or f"Task {i + 1}"
        status      = "Completed" if t.get("is_labeled") else "Pending"
        annotations = t.get("annotations") or []
        annotator   = "-"
        if annotations:
            completed_by = annotations[0].get("completed_by", {})
            if isinstance(completed_by, dict):
                annotator = completed_by.get("email", "-") or "-"

        updated_raw = t.get("updated_at", "") or ""
        rows.append({
            "Task ID":    f"#{t.get('id', i):06d}",
            "Title":      title_text,
            "Owner_name": t.get("owner_name"),
            "Status":     status,
            "Annotator":  annotator,
            "Updated":    updated_raw[:10],
            "Score":      round(t.get("avg_lead_time", 0) or 0, 2),
        })

    return pd.DataFrame(rows)


def _extract_task_doc(task, project_name: str) -> dict:
   
    task_dict = {}
    try:
        if hasattr(task, "model_dump"):
            task_dict = task.model_dump() or {}
    except Exception:
        logger.debug(
            "_extract_task_doc: model_dump() failed for task %s, falling back to {}",
            getattr(task, "id", "?"),
        )

    status = "Completed" if bool(getattr(task, "is_labeled", False)) else "Pending"

    owner = "-"

    created_by_dict = task_dict.get("created_by")
    if created_by_dict is not None and isinstance(created_by_dict, dict):
        email = created_by_dict.get("email")
        if email:
            owner = str(email)

    if owner == "-":
        cb_attr = getattr(task, "created_by", None)
        if cb_attr is not None:
            email = getattr(cb_attr, "email", None)
            if email:
                owner = str(email)

    if owner == "-":
        fallback = (
            getattr(task, "created_username", None)
            or task_dict.get("created_username")
        )
        if fallback:
            owner = str(fallback)

    annotations_dumped = task_dict.get("annotations") or []
    annotator    = "-"
    completed_at = "-"
    if annotations_dumped:
        first_ann     = annotations_dumped[0]
        raw_completed = str(first_ann.get("created_at") or "")
        completed_at  = raw_completed[:10] if raw_completed else "-"

        cb = first_ann.get("completed_by")
        if cb is not None and isinstance(cb, dict):
            annotator = cb.get("email") or "-"
        elif cb is not None:
            annotator = str(cb)

    updated_raw = str(getattr(task, "updated_at", "") or "")

    return {
        "task_id":      f"#{task.id:06d}",
        "project_name": project_name,
        "owner":        owner,
        "annotator":    annotator,
        "completed_at": completed_at,
        "status":       status,
        "updated":      updated_raw[:10],
    }


def store_mongodb(api_url: str, api_token: str, mongodb_url: str,
                  project_title: str, project_id: int | str) -> None:
   
    logger.info("store_mongodb: starting sync for project '%s' (id=%s)", project_title, project_id)

    if not api_url or not api_token:
        logger.error("store_mongodb: api_url and api_token are required")
        return

    if not api_url.startswith(("http://", "https://")):
        logger.error("store_mongodb: invalid api_url '%s' — must start with http(s)://", api_url)
        raise ValueError("Label Studio URL must start with http:// or https://")

    logger.debug("store_mongodb: connecting to Label Studio at %s", api_url)
    client_lst = make_client(api_url, api_token)

    logger.debug("store_mongodb: connecting to MongoDB")
    client_mongo = MongoClient(mongodb_url)
    database     = client_mongo["All_selected_projects"]
    collection   = database[project_title]

    logger.info("store_mongodb: fetching tasks from Label Studio for project %s", project_id)
    raw_tasks = list(client_lst.tasks.list(project=project_id))
    logger.info("store_mongodb: fetched %d tasks from Label Studio", len(raw_tasks))

    if not raw_tasks:
        logger.warning("store_mongodb: no tasks found for project '%s' — nothing stored", project_title)
        return

    docs = [_extract_task_doc(t, project_title) for t in raw_tasks]
    logger.debug("store_mongodb: built %d slim documents", len(docs))

    from pymongo import UpdateOne
    operations = [
        UpdateOne({"task_id": doc["task_id"]}, {"$set": doc}, upsert=True)
        for doc in docs
    ]
    result = collection.bulk_write(operations)
    logger.info(
        "store_mongodb: upsert complete — inserted=%d, modified=%d, matched=%d",
        result.upserted_count,
        result.modified_count,
        result.matched_count,
    )
    logger.info("store_mongodb: sync finished for project '%s'", project_title)


def fetch_mongo( project_title: str) -> pd.DataFrame:
    logger.info("fetch_mongo: fetching documents from collection '%s'", project_title)
    client     = MongoClient(mongodb_url())
    database   = client["All_selected_projects"]
    collection = database[project_title]

    documents = list(collection.find({}, {"_id": 0}))
    logger.info("fetch_mongo: retrieved %d documents from '%s'", len(documents), project_title)
    return pd.DataFrame(documents)
