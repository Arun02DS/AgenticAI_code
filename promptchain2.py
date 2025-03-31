from groq import Groq
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Function to fetch weather details
def get_weather(location:str) -> dict:
    """
    Fetches weather data for the specified location using OpenWeather API.
    """
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": os.getenv("OPENWEATHER_API_KEY"),
        "units": "metric"
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return {
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
            'name': data['name']
        }
    else:
        return {"error": f"Error: {response.status_code} - {response.text}"}

def tool_calling(city:str)->str:
    """ Function to call for a specific city to get wheater"""
    # Initialize Groq client

    # Tool metadata
    tools = [
        {
            "type": "function",
            "function": {
                "name": "compare_weather",
                "description": "Compare the current weather of two cities",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city1": {
                            "type": "string",
                            "description": "Name of the first city"
                        },
                        "city2": {
                            "type": "string",
                            "description": "Name of the second city"
                        },
                    },
                    "required": ["city1", "city2"]
                }
            }
        }
    ]

    # Step 1: Define the system prompt
    initial_prompt = [
        {
            "role": "system",
            "content": "You are an expert weather assistant.write a wheater report for news channel."
        },
        {
            "role": "user",
            "content": f"what is the wheather in the {city}."
        }
    ]

    # Step 2: Generate initial response with tool calls
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=initial_prompt,
        tools=tools,
        tool_choice="auto",
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stop=None
    )

    if completion.choices[0].message.tool_calls:
        
        tool_call = completion.choices[0].message.tool_calls[0]
        # Extract arguments for the tool call
        function_args = json.loads(tool_call.function.arguments) 
        location = function_args.get('location')

        weather_data = get_weather(location)

        # Generate the final response
        second_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
            "role": "system",
            "content": "You are an expert weather assistant.write a wheater report for news channel."},
        {
            "role": "user",
            "content": f"what is the wheather in the {city}."},
            completion.choices[0].message,
            {
                "role": "tool",
                "content": json.dumps(weather_data),
                "tool_call_id": tool_call.id
            }
            ]
        )

        
        return second_completion.choices[0].message.content

# weather1 = tool_calling("Delhi")
# print(weather1)

def text_generation(prompt):
    """
    This function generate text with provided prompt
    """
    # Step 2: Generate initial response with tool calls
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        
    )

    return completion.choices[0].message.content


weather1 = tool_calling("Delhi")
compare_weather = text_generation(f"Weather in delhi {weather1},show only data analysis between Mumbai and Delhi.")
print(compare_weather)
