from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from datetime import datetime
import os
import random
import json
import numpy as np
import pickle
import bcrypt
import nltk
from nltk.stem import WordNetLemmatizer
import tensorflow as tf
import logging

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'lAjnf893lszdk$&lma1-Pgl$'  # Secret key for session management

# Configure logging
logging.basicConfig(filename='chatbot.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# MongoDB connection string and database name
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "chatbot_db"

# Initialize MongoDB client and database
def get_db():
    client = MongoClient(MONGO_URI)  # Connect to MongoDB
    db = client[DATABASE_NAME]       # Select database
    return db

# Check if the database is initialized (e.g., if a collection exists)
def is_db_initialized(db):
    return "intents" in db.list_collection_names()

# Load the trained model and other necessary data
lemmatizer = WordNetLemmatizer()  # Initialize lemmatizer
model = tf.keras.models.load_model('chatbot_model.h5')  # Load trained model
words = pickle.load(open('words.pkl', 'rb'))  # Load words
classes = pickle.load(open('classes.pkl', 'rb'))  # Load classes

@app.route('/')
def home():
    return render_template('index.html')  # Render homepage

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        users_collection = db["users"]
        username = request.form['username']
        password = request.form['password']
        
        if users_collection.find_one({"username": username}):
            flash("Username already exists!")
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({"username": username, "password": hashed_password})
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        users_collection = db["users"]
        username = request.form['username']
        password = request.form['password']
        
        user = users_collection.find_one({"username": username})
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['username'] = username
            flash("Login successful!")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('home'))

@app.route('/chat', methods=['POST'])
def chat():
    if 'username' not in session:
        flash("Please log in to chat.")
        return redirect(url_for('login'))
    
    user_message = request.form['message']
    response = generate_response(user_message)
    save_message_to_db(user_message, response)
    log_message(user_message, response)  # Log the message and response
    return render_template('index.html', user_message=user_message, response=response)

def log_message(user_message, response):
    logging.info(f'User: {user_message} | Bot: {response}')  # Log user message and bot response

def preprocess_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)  # Tokenize the sentence
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]  # Lemmatize each word
    return sentence_words

def bag_of_words(sentence):
    sentence_words = preprocess_sentence(sentence)  # Preprocess the sentence
    bag = [0] * len(words)  # Initialize bag of words with zeros
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1  # Mark the word's position as 1
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)  # Get bag of words for the sentence
    res = model.predict(np.array([bow]))[0]  # Predict the class probabilities
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]  # Filter out low probability results

    results.sort(key=lambda x: x[1], reverse=True)  # Sort by probability in descending order
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})  # Append intent and probability to the list
    logging.info(f'Predicted intents for "{sentence}": {return_list}')  # Log predicted intents
    return return_list

def generate_response(message):
    intents = predict_class(message)  # Predict the class of the message
    if intents:
        intent = intents[0]['intent']
        db = get_db()
        intent_data = db["intents"].find_one({"intent": intent})  # Fetch intent data from the database
        logging.info(f'Fetched intent data for "{intent}": {intent_data}')  # Log the fetched intent data
        if intent_data:
            response = random.choice(intent_data['responses'])  # Select a random response
            logging.info(f'Selected response: {response}')  # Log the selected response
            return response
    return "I'm not sure how to respond to that."

def save_message_to_db(user_message, response):
    db = get_db()
    messages_collection = db["messages"]
    message_document = {
        "username": session['username'],  # Use logged-in username
        "message": user_message,
        "response": response,
        "timestamp": datetime.utcnow()
    }
    messages_collection.insert_one(message_document)  # Insert the message document into the database

if __name__ == "__main__":
    db = get_db()
    if not is_db_initialized(db):
        os.system('python setup_db.py')  # Run the setup script if the database is not initialized
    
    app.run(debug=True)  # Start the Flask application in debug mode
