import json
import openai
import random
import os
import time
import requests
import sqlite3

config_path = os.path.join(os.path.dirname(__file__), '..\config.json')
with open(config_path) as config_file:
    config = json.load(config_file)

NEWS_API_KEY = config['NEWS_API_KEY']
NEWS_BASE_URL = config['NEWS_BASE_URL']

QUOTE_BASE_URL = config['QUOTE_BASE_URL']

openai.api_key = config['OPEN_API_KEY']

conn = sqlite3.connect(config['conn'])

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_random_quote",
            "description": "Fetches a random quote and author",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "get_top_headlines",
        "description": "Fetches the top news headlines for a given country and category.",
        "parameters": {
            "type": "object",
            "properties": {
                "country": {
                    "type": "string",
                    "description": "The 2-letter country code (ISO 3166-1) for which you want to get the news headlines. Default is 'us'",
                    "default": "us"
                },
                "category": {
                    "type": "string",
                    "description": "The category of news to fetch, such as 'general', 'business', 'entertainment', 'health', 'science', 'sports', or 'technology'. Default is 'general'.",
                    "enum": ["general", "business", "entertainment", "health", "science", "sports", "technology"],
                    "default": "general"
                }
            },
            "required": []
        }
    }
    },
    {
        "type": "function",
        "function": {
            "name": "add_task_to_db",
            "description": "Add a task to the to-do list",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The task to add"
                    }
                },
                "required": ["task"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_tasks_from_db",
            "description": "Retrieve all tasks from the to-do list",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_task_status_in_db",
            "description": "Update the status of a task in the to-do list",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The ID of the task to update"
                    },
                    "new_status": {
                        "type": "string",
                        "description": "The new status of the task (e.g., 'completed', 'pending')"
                    }
                },
                "required": ["task_id", "new_status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task_from_db",
            "description": "Delete a task from the to-do list",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The ID of the task to delete"
                    }
                },
                "required": ["task_id"]
            }
        }
    }
]
# Create assistant
assistant = openai.beta.assistants.create(
    name="Custom Tool Assistant",
    instructions="You are a helpful assistant",
    model="gpt-4o-mini",
    tools=tools)
print(f"Assistant created with ID: {assistant.id}")

# add your own functions
def get_random_quote():
    
    response = requests.get(QUOTE_BASE_URL)

    if response.status_code == 200:
        data = response.json()
        
        quoteData = data[0]['q']  
        authorData = data[0]['a'] 
        quote = quoteData + ' - ' + authorData + '\n'
        print(quote)
        return quote
    
def get_top_headlines(country='us', category='general'):
    #Params for news
    params = {
        'apiKey': NEWS_API_KEY,   
        'country': country,  
        'category': category,  
        'pageSize': 5
    }

    response = requests.get(NEWS_BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        articles = data.get('articles', [])
        
        if articles:
            news= f"Top {category.capitalize()} News Headlines in {country.upper()}:\n"
            for idx, article in enumerate(articles):
                if(article['title'] != '[Removed]'):
                    news = news + article['title']
                
        else:
            return "No news articles found."
    else:
        print(f"Failed to fetch news. Status code: {response.status_code}")
    return news

def add_task_to_db(task):
    
    c = conn.cursor()
    c.execute('INSERT INTO tasks (task, status) VALUES (?, ?)', (task, 'pending'))
    conn.commit()
    conn.close()

def get_tasks_from_db():
    
    c = conn.cursor()
    c.execute('SELECT id, task, status FROM tasks')
    tasks = c.fetchall()
    conn.close()
    if tasks:
        return tasks
    else:
        return []

# Function to update task status in the database
def update_task_status_in_db(task_id, new_status):
    
    c = conn.cursor()
    c.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, task_id))
    conn.commit()
    conn.close()

# Function to delete a task from the tasks table
def delete_task_from_db(task_id):
    
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

# Create a conversation thread
thread = openai.beta.threads.create()
print(f"Thread created with ID: {thread.id}")

def interact_with_assistant(user_input):
    print("assistent")
    message = openai.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    #content="Please give me a todays qoute and tell me the output"
    #content="Please give me todays news and tell me the output"
    content = user_input
    )
    
    # Run the assistant
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    # Wait for the run to complete
    attempt = 1
    while run.status != "completed":
        #print(f"Run status: {run.status}, attempt: {attempt}")
        run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run.status == "requires_action":
            break

        if run.status == "failed":
            # Handle the error message if it exists
            if hasattr(run, 'last_error') and run.last_error is not None:
                error_message = run.last_error.message
            else:
                error_message = "No error message found..."

            print(f"Run {run.id} failed! Status: {run.status}\n  thread_id: {run.thread_id}\n  assistant_id: {run.assistant_id}\n  error_message: {error_message}")
            print(str(run))

        attempt += 1
        time.sleep(5)

    # status "requires_action" means that the assistant decided it needs to call an external tool
    # assistant gives us names of tools it needs, we call the corresponding function and return the data back to the assistant
    if run.status == "requires_action":
        print("Run requires action, assistant wants to use a tool")
        if run.required_action:
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                if tool_call.function.name == "add_task_to_db":
                    print("  add_task_to_db called")
                    
                    task = json.loads(run.required_action.submit_tool_outputs.tool_calls[0].function.arguments).get('task')
                    output = add_task_to_db(task = task)
                elif tool_call.function.name == "get_tasks_from_db":
                    tasks = get_tasks_from_db()
                    if tasks:
                        output = "Here are your tasks:\n"
                        for task_id, task, status in tasks:
                            output += f"{task_id}: {task} - {status}\n"
                    else:
                        output = "Your to-do list is empty."

                elif tool_call.function.name == "update_task_status_in_db":
                    
                    task_id = json.loads(run.required_action.submit_tool_outputs.tool_calls[0].function.arguments).get('task_id')
                    new_status = json.loads(run.required_action.submit_tool_outputs.tool_calls[0].function.arguments).get('new_status')
                    print(f"Updating task {task_id} status to {new_status}")
                    update_task_status_in_db(task_id, new_status)
                    output = f"Task {task_id} status updated to '{new_status}'."

                elif tool_call.function.name == "delete_task_from_db":
                    task_id = json.loads(run.required_action.submit_tool_outputs.tool_calls[0].function.arguments).get('task_id')
                    print(f"Deleting task {task_id}")
                    delete_task_from_db(task_id)
                    output = f"Task {task_id} deleted."
                elif tool_call.function.name == "get_random_quote":
                    print("  get_random_quote called")
                    output = get_random_quote()
                elif tool_call.function.name == "get_top_headlines":
                    print("  get_top_headlines called")
                    output = get_top_headlines()
                else:
                    print("Unknown function call")
                #print(f"  Generated output: {output}")

                # submit the output back to assistant
                openai.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=[{
                        "tool_call_id": tool_call.id,
                        "output": str(output)
                    }]
                )
                

    if run.status == "requires_action":

        # After submitting tool outputs, we need to wait for the run to complete, again
        run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        attempt = 1
        while run.status not in ["completed", "failed"]:
            #print(f"Run status: {run.status}, attempt: {attempt}")
            time.sleep(2)
            run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            attempt += 1

    if run.status == "completed":
        # Retrieve and print the assistant's response
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        final_answer = messages.data[0].content[0].text.value
        #print(f"=========\n{final_answer}")
    elif run.status == "failed":
        # Handle the error message if it exists
        if hasattr(run, 'last_error') and run.last_error is not None:
            error_message = run.last_error.message
        else:
            error_message = "No error message found..."

        print(f"Run {run.id} failed! Status: {run.status}\n  thread_id: {run.thread_id}\n  assistant_id: {run.assistant_id}\n  error_message: {error_message}")
        print(str(run))
    else:
        print(f"Unexpected run status: {run.status}")
    
    return {thread.id, final_answer}




if __name__ == "__main__":
    print("chatBot: Hello! How can I assist you today?")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("chatBot: Goodbye!")
            break
        
        # Get the assistant's response
        response = interact_with_assistant(user_input)
        print(f"chatBot: {response}")