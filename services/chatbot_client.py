import requests

CHATBOT_URL = "http://localhost:8000/chat"

def ask_chatbot(message, session_id):
    payload = {
        "message": message,
        "session_id": session_id
    }

    response = requests.post(
        CHATBOT_URL,
        json=payload
    )

    return response.json()