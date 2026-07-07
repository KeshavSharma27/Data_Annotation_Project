from fastapi import FastAPI
from backend.routes.tasks import router as task_router
from backend.routes.chat import router as chat_router
from backend.routes.labelstudio import router as labelstudio_router

app = FastAPI()

app.include_router(task_router)
app.include_router(chat_router)
app.include_router(labelstudio_router)

@app.get("/")
def home():
    return {"message": "Data Annotation API Running"}


