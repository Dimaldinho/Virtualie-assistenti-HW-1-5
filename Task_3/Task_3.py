import json
import openai
import random
import os
import time
import requests

# Set your OpenAI API key
# this key has auto-charge disabled, no billing methog assigned, and 5$ in API credits.
# Ideally, you should use your own OpenAI account, and your own money

config_path = os.path.join(os.path.dirname(__file__), '..\config.json')
with open(config_path) as config_file:
    config = json.load(config_file)

NEWS_API_KEY = config['NEWS_API_KEY']
NEWS_BASE_URL = config['NEWS_BASE_URL']

QUOTE_BASE_URL = config['QUOTE_BASE_URL']

openai.api_key = config['OPEN_API_KEY']


# Define the custom tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "return_string",
            "description": "Returns a random text string",
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
            "name": "return_integer",
            "description": "Returns an integer from 0 to 9",
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
                    "description": "The 2-letter country code (ISO 3166-1) for which you want to get the news headlines.",
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
    }
]

# 40-mini is the cheapest one.
assistant = openai.beta.assistants.create(
    name="Custom Tool Assistant",
    instructions="You are a helpful assistant that uses tools to provide specific information. When a user asks for a quote, fetch it using get_random_quote and For news, use get_top_headlines default to Latvia with general news.",
    model="gpt-4o-mini",
    tools=tools
)

print(f"Assistant created with ID: {assistant.id}")

# Define the tool functions
def return_string():
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=5))

def return_integer():
    return random.randint(0, 9)

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

# Create a conversation thread
thread = openai.beta.threads.create()
print(f"Thread created with ID: {thread.id}")

# Add a message to the thread
contentInput = input("Input your query: ")
print("Submitting your query to assistant")
message = openai.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    #content="Please give me a todays qoute and tell me the output"
    #content="Please give me todays news and tell me the output"
    content = contentInput
)

# Run the assistant
run = openai.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id
)

# Wait for the run to complete
attempt = 1
while run.status != "completed":
    print(f"Run status: {run.status}, attempt: {attempt}")
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

    # Process tool calls
    if run.required_action:
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            
            if tool_call.function.name == "return_string":
                print("  return_string called")
                output = return_string()
            elif tool_call.function.name == "return_integer":
                print("  return_integer called")
                output = return_integer()
            elif tool_call.function.name == "get_random_quote":
                print("  get_random_quote called")
                output = get_random_quote()
            elif tool_call.function.name == "get_top_headlines":
                print("  get_top_headlines called")
                output = get_top_headlines()
            else:
                print("Unknown function call")
            print(f"  Generated output: {output}")

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
        print(f"Run status: {run.status}, attempt: {attempt}")
        time.sleep(2)
        run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        attempt += 1

if run.status == "completed":
    # Retrieve and print the assistant's response
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    final_answer = messages.data[0].content[0].text.value
    print(f"=========\n{final_answer}")
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