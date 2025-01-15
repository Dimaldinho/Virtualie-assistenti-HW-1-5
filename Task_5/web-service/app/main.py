import json
import os
import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel
import assistant
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:8081",  # React Native web app
    "http://127.0.0.1:8081",  # Alternative localhost
]


# Load configuration from JSON file
config_path = os.path.join(os.path.dirname(__file__),'..', "..", "..", "config.json")

# Convert to an absolute path
config_path = os.path.abspath(config_path)

with open(config_path) as config_file:
    config = json.load(config_file)

thread_id = config["thread_id"]
if not thread_id:
    raise ValueError("Thread ID not found in config.json. Please ensure it is properly initialized.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Model for a single message
class Message(BaseModel):
    role: str
    content: str

# Receive a dummy message and return a test response from the virtual assistant
@app.post("/send-message/")
async def process_message_and_respond(message: str):
    connection = sqlite3.connect("message-history.db")
    cursor = connection.cursor()
    print("AAAAAA = ", message)
    # Save user message to the database
    cursor.execute('''
        INSERT INTO messages (thread_id, role, content)
        VALUES (?, ?, ?)
    ''', (thread_id, "user", message))

    # Get the assistant's response
    a_response = assistant.interact_with_assistant(message)
    response_message = a_response["response"]

    # Save the assistant's response to the database
    cursor.execute('''
        INSERT INTO messages (thread_id, role, content)
        VALUES (?, ?, ?)
    ''', (thread_id, "assistant", response_message))

    # Commit changes and close the connection
    connection.commit()
    connection.close()
    
    return {
        "thread_id": thread_id,
        "response": response_message,
        "message_received": message
    }

# Retrieve a conversation history based on the thread ID, 5 messages from the user, 5 from the assistant

@app.get("/conversation-history/")
async def conversation_history(thread_id: str):
    connection = sqlite3.connect("message-history.db")
    cursor = connection.cursor()

    # Fetch messages from the database
    cursor.execute('''
        SELECT role, content FROM messages
        WHERE thread_id = ?
        ORDER BY created_at ASC
    ''', (thread_id,))
    rows = cursor.fetchall()
    print(rows)
    # Format the conversation history
    conversation_history = [{"sender": row[0], "content": row[1]} for row in rows]
    
    connection.commit()
    connection.close()

    return {
        "thread_id": thread_id,
        "conversation_history": conversation_history
    }
