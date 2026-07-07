from fastapi import APIRouter
from backend.retrieve_task import fetch_projects
from backend.retrieve_task import fetch_tasks

router = APIRouter()

@router.post("/projects")
def get_projects(payload: dict):

    projects, error = fetch_projects(
        payload["api_url"],
        payload["api_token"]
    )

    return {
        "projects": projects,
        "error": error
    }


@router.post("/tasks")
def get_tasks(payload: dict):

    tasks = fetch_tasks(
        api_url=payload["api_url"],
        api_token=payload["api_token"],
        project_id=payload["project_id"]
    )

    return {"tasks": tasks}