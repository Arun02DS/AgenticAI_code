from groq import Groq
import os
from dotenv import load_dotenv
import requests
import json
import asyncio
import concurrent.futures

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def llm_agent(prompt,system_prompt="you are an helpful assistant"): 
    """ Base LLM function to answer user input"""
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt,},
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="mixtral-8x7b-32768",
    )
    return chat_completion.choices[0].message.content

def parallel_llm_processing(user_prompt):
    """
    processes the 3 agents in parallel
    - Agent 1 - Focuses in factual analysis.
    - Agent 2 - Focuses in craetive solutions.
    - Agent 3 - Synthesizes both responses
    
    """
    agent1_system = "You are an analytical assistant focusing on providing factual,detailed analysis."
    agent2_system = "You are a creative assistant focusing on generating innovative solutions and prespective."

    # Run first two agents in parallel with threadpooling
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future1 = executor.submit(llm_agent, user_prompt, agent1_system)
        future2 = executor.submit(llm_agent, user_prompt, agent2_system)

        agent1_response = future1.result()
        agent2_response = future2.result()

        synthesis_prompt = f"""Synthesize and analyse the following responses into a cohesive analysis:
        \n\nAgent 1 Response: {agent1_response}
        \n\nAgent 2 Response: {agent2_response} 
        Provide a balanced and complete answer that incorporate insights from both responses."""

        final_response = llm_agent(synthesis_prompt,"You are a balanced assistant that synthesizes different perspectives.")

        return {
            "agent1_response": agent1_response,
            "agent2_response": agent2_response,
            "final_response": final_response
        }

if __name__ == "__main__":
    user_prompt = "why apples are red?"
    results = parallel_llm_processing(user_prompt)
    print('agent1_response :')
    print(results['agent1_response'])
    print('agent2_response :')
    print(results['agent2_response'])
    print('final_response :')
    print(results['final_response'])