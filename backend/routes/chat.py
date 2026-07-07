from fastapi import APIRouter
import requests

router = APIRouter()

@router.post("/chat")
def chat(payload: dict):

    response = requests.post(
        "http://localhost:8000/chat",
        json=payload
    )

    return response.json()