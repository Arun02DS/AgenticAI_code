from groq import Groq
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

# Function to fetch weather details
def get_weather(location) -> dict:
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


# Function to compare weather between two cities
def compare_weather(city1: str, city2: str) -> dict:
    """
    Compares the weather of two cities and returns a summary.
    """
    weather1 = get_weather(city1)
    weather2 = get_weather(city2)

    if "error" in weather1 or "error" in weather2:
        return {
            "error": weather1.get("error", "") + " " + weather2.get("error", "")
        }

    comparison = {
        "city1": {
            "name": weather1['name'],
            "temperature": weather1['temperature'],
            "description": weather1['description'],
            "humidity": weather1['humidity']
        },
        "city2": {
            "name": weather2['name'],
            "temperature": weather2['temperature'],
            "description": weather2['description'],
            "humidity": weather2['humidity']
        }
    }

    return comparison


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

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Step 1: Define the system prompt
initial_prompt = [
    {
        "role": "system",
        "content": "You are a witty weather assistant. Compare the weather of two cities and respond with a humorous twist."
    },
    {
        "role": "user",
        "content": "Compare the weather between Mumbai and Delhi."
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

# Step 3: Process tool calls and chain prompts
if completion.choices[0].message.tool_calls:
    for tool_call in completion.choices[0].message.tool_calls:
        if tool_call.function.name == "compare_weather":
            # Extract arguments for the tool call
            args = eval(tool_call.function.arguments)  # Parse arguments
            weather_comparison = compare_weather(args['city1'], args['city2'])

            # Chain the response
            chained_prompt = initial_prompt + [
                completion.choices[0].message,
                {
                    "role": "tool",
                    "content": json.dumps(weather_comparison),
                    "tool_call_id": tool_call.id
                }
            ]

            # Generate the final response
            second_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=chained_prompt,
                temperature=1,
                max_tokens=1024,
                top_p=1,
                stop=None,
            )

            # Print the humorous comparison
            print(second_completion.choices[0].message.content)
else:
    print("No tool calls found.")
