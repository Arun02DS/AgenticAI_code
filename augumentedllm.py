from groq import Groq
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()


def get_weather(location)->dict:

    base_url="https://api.openweathermap.org/data/2.5/weather"

    params= {
        "q":location,
        "appid":os.getenv("OPENWEATHER_API_KEY"),
        "units": "metric"
    }

    respones = requests.get(base_url, params=params)
    if respones.status_code == 200:
        data = respones.json()
        return {
            'temperature':data['main']['temp'],
            'description':data['weather'][0]['description'],
            'humidity':data['main']['humidity'],
            'name':data['name']
        }
    else:
        return {f"Error: {respones.status_code} - {respones.text}"}

# print(get_weather("delhi"))
tools = [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "Name of the city"
            },
          },
          "required": ["location"]
        }
      }
    }
  ]

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "system",
            "content": "you are a weather assistant. Get the weather using tools. return response as a joke.",
        },
        {
            "role": "user",
            "content": "Get weather for the location mumbai",
        },
    ],
    tools=tools,
    tool_choice="auto",
    temperature=1,
    max_tokens=1024,
    top_p=1,
    stop=None,
)

if completion.choices[0].message.tool_calls:
    for tool_call in completion.choices[0].message.tool_calls:
        if tool_call.function.name == "get_weather":
            args = tool_call.function.arguments
            args = eval(args)
            # print(args)
            # print(get_weather(location=args['location']))
        
        second_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                "role": "system",
                "content": "you are a weather assistant. Get the weather using tools. return response as a joke.",
                },
                {
                    "role": "user",
                    "content": f"Get weather for the location mumbai",
                },
                completion.choices[0].message,
                {
                    "role": "tool",
                    "content": json.dumps(get_weather(args['location'])),
                    "tool_call_id": tool_call.id
                }
            ],
            
        )
        print(second_completion.choices[0].message.content)
else:
    print("No tool calls found")


