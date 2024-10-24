from fastapi import FastAPI
from pydantic import BaseModel
import assistant

app = FastAPI()

# Model for a single message
class Message(BaseModel):
    role: str
    content: str

# Receive a dummy message and return a test response from the virtual assistant
@app.post("/send-message/")
async def process_message_and_respond(message: str):
    """
    Receive a message from the user and return a test response from the virtual assistant.

    Args:
        thread_id (str): The ID of the conversation thread.
        message (str): The message sent by the user.

    Returns:
        dict: A dictionary containing the thread ID, the assistant's test response, and the original message.
    """


    thread_id = assistant.interact_with_assistant(message)
    print(list(thread_id)[0])
    # Currently returns dummy data.
    # Goal: your actual method should add the user message to the conversation history,
    # and also return a response from the assistant
    return {
        "thread_id": list(thread_id)[0],
        "response": list(thread_id)[1],
        "message_received": message
    }

# Retrieve a conversation history based on the thread ID, 5 messages from the user, 5 from the assistant
@app.get("/conversation-history/")
async def conversation_history(thread_id: str):
    """
    Retrieve the conversation history for a specific thread.

    Args:
        thread_id (str): The ID of the conversation thread.

    Returns:
        dict: A dictionary containing the thread ID and a list of conversation messages, including both user and assistant messages.
    """

    # Fill the message history with dummy messages
    user_messages = [f"User message {i} in thread {thread_id}" for i in range(1, 6)]
    assistant_messages = [f"Assistant message {i} in thread {thread_id}" for i in range(1, 6)]
    conversation_history = []
    for i in range(5):
        conversation_history.append({"sender": "user", "content": user_messages[i]})
        conversation_history.append({"sender": "assistant", "content": assistant_messages[i]})

    return {
        "thread_id": thread_id,
        "conversation_history": conversation_history
    }