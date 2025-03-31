from groq import Groq
import os
from dotenv import load_dotenv
import requests
import json
import asyncio
import concurrent.futures

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def orchestrator(task):
    """ Orchestrator that breaks down the task and coordinate workers"""

    orchestrator_prompt = f"""
        you are an orchestrator that breaks down th tasks into subtasks. Analyse the following tasks
        and break it down into 2 subtasks that can handled by the workers.
        Return the subtask in a clear and numbered foramt.

        Task={task}
    
    """

    planning_response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a task orchestrator.",
            },
            {
                "role": "user",
                "content": orchestrator_prompt.format(task=task),
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    subtasks = planning_response.choices[0].message.content
    print(subtasks)

    worker1_result = worker(subtasks,1)
    worker2_result = worker(subtasks, 2)

    synthesis_prompt = f"""Synthesize and analyse the following responses into a cohesive analysis:
        \n\nWorker 1 Response: {worker1_result}
        \n\nWorker 2 Response: {worker2_result} 
        Provide a balanced and complete answer that incorporate insights from both responses."""

    final_response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a result synthesizer.",
            },
            {
                "role": "user",
                "content": synthesis_prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    return final_response.choices[0].message.content

def worker(subtask, worker_id):
    """ Worker that performs the subtasks"""
    worker_prompt = f"""
        You are a worker that performs and completes the subtask.
        Task={subtask}
        Worker ID={worker_id}
    """

    worker_response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"You are a worker #{worker_id}, focused on your specific task.",
            },
            {
                "role": "user",
                "content": worker_prompt.format(subtask=subtask, worker_id=worker_id),
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    return worker_response.choices[0].message.content

def llm_agent(prompt):
    """
        main entry point that uses the orchestrator and worker to process the task
    """
    task = prompt
    result = orchestrator(task)
    return result

result = llm_agent("write and provide code in python to summarize text with evaluation")
print(result)