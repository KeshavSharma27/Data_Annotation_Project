from fastapi import APIRouter

router = APIRouter()

@router.get("/tasks")
def get_tasks():
    return [
        {"id": 1, "name": "Task A"},
        {"id": 2, "name": "Task B"}
    ]