from pymongo import MongoClient
from datetime import datetime
import json

# MongoDB connection string
MONGO_URI = "mongodb://localhost:27017"

# Database name
DATABASE_NAME = "chatbot_db"

def create_database_and_collections():
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    
    # Create database
    db = client[DATABASE_NAME]
    
    # Create collections
    users_collection = db["users"]
    messages_collection = db["messages"]
    intents_collection = db["intents"]
    
    # Define sample documents
    user_sample = {
        "user_id": 1,
        "name": "John Doe",
        "created_at": datetime.utcnow()
    }
    
    message_sample = {
        "message_id": 1,
        "user_id": 1,
        "message": "Hello, how can I help you?",
        "timestamp": datetime.utcnow()
    }
    
    # Insert sample documents
    users_collection.insert_one(user_sample)
    messages_collection.insert_one(message_sample)
    
    print("Database and collections created successfully with sample data.")

def load_intents():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    intents_collection = db["intents"]

    with open('intents.json', 'r') as file:
        data = json.load(file)
        intents_collection.insert_many(data['intents'])

    print("Intents loaded successfully.")

if __name__ == "__main__":
    create_database_and_collections()
    load_intents()
