from pymongo import MongoClient
import json

# MongoDB connection string
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "chatbot_db"

def load_intents():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    intents_collection = db["intents"]

    with open('intents.json', 'r') as file:
        data = json.load(file)
        intents_collection.insert_many(data['intents'])

    print("Intents loaded successfully.")

if __name__ == "__main__":
    load_intents()
