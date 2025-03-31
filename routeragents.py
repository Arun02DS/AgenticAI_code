from groq import Groq
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def router_agent(prompt):
    """
    This function provided correct route to user query
    """
    
    route_res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are an expert LLM router Agent.You only job is to decide which LLM agent should be used for user query.
                                Respond only with either "reasoning" or "conversational" based on the following rules.
                                - Response should be "reasoning" if :
                                    * Query requires extensive reasoning.
                                    * Query involves maths ans coding.
                                - Response should be "conversational" if : 
                                    * Query is casual chat or greeting.
                                    * Query needs simple conversational response."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        
    )

    route_to = route_res.choices[0].message.content.strip().lower()
    print(route_to)
    if route_to == "reasoning":
        return reasoning_agent(prompt)
    else: 
        return conversational_agent(prompt)

def reasoning_agent(prompt):
    """
    This function generate text If extensive reasoning is needed.
    """
    # Step 2: Generate initial response with tool calls
    completion = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {
                "role": "system",
                "content": """You are an expert reasoning agent.You have to answer the user reasoning, maths and coding queries."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

    )

    return completion.choices[0].message.content

def conversational_agent(prompt):
    """
    This function generate text when user needed to converse with the AI.
    """

    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "system",
                "content": """You are an expert conversational agent.You have to converse with the user input."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

    )

    return completion.choices[0].message.content

print(router_agent("hello"))
print(router_agent("write a code for reverse a string"))