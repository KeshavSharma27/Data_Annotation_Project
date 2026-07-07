from label_studio_sdk import LabelStudio
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
mongodb_url = os.getenv("MONGODB_TOKEN")

def config():
    try:
        client_mongodb = MongoClient(mongodb_url)
        database = client_mongodb['Sentiments']
        collections = database.list.collection_names()
        return collections
    except Exception as NetworkError:
        print("There is a problem in connecting to mongodb ")

    return False
    
