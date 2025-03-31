from groq import Groq
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def evaluate_code(code):
    """
    Evaluates the provided Python code and returns feedback.

    Args:
        code (str): The Python code to evaluate.

    Returns:
        tuple: A tuple containing a boolean indicating pass/fail and feedback (str).
    """
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior code evaluator. Evaluate the given Python code for quality, best practices, and potential issues. "
                               "Provide a response with your evaluation."
                },
                {
                    "role": "user",
                    "content": f"Please evaluate the following code:\n\n```{code}```",
                }
            ],
            model=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
        )

        # Debugging: Log raw response
        # print("Raw API response:", response)

        result = response.choices[0].message.content.strip()

        # Try to extract pass/fail and feedback from response
        if "pass" in result.lower() or "fail" in result.lower():
            passed = "pass" in result.lower()
            feedback_start = result.find("\n")  # Start after first line
            feedback = result[feedback_start:].strip() if feedback_start != -1 else "No feedback provided."
            return passed, feedback

        # Fallback for unexpected response formats
        return False, "Unable to determine pass/fail status. Please review the following response:\n" + result

    except Exception as e:
        raise RuntimeError(f"Error evaluating code: {e}")

def optimize_code(code, feedback):
    """
    Optimizes the provided code based on feedback.

    Args:
        code (str): The original code.
        feedback (str): Feedback for improving the code.

    Returns:
        str: The optimized code.
    """
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a code optimizer. Analyze the feedback and suggest improvements to the code."
                },
                {
                    "role": "user",
                    "content": f"Original code:\n\n```{code}```\n\nFeedback:\n\n{feedback}",
                }
            ],
            model=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Error optimizing code: {e}")

def llm_agent(prompt, max_iteration=3):
    """
    Implements evaluator-optimizer workflow for code generation and refinement.

    Args:
        prompt (str): Prompt describing the code to be generated.
        max_iteration (int): Maximum number of iterations for refinement.

    Returns:
        str: Final optimized code after evaluation and iteration.
    """
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a code generator. Generate code based on the given prompt."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
        )
        current_code = response.choices[0].message.content.strip()

        for iteration in range(max_iteration):
            print(f"\nIteration {iteration + 1} code:")
            print("---------------------")
            print(current_code)

            print("Evaluating code...")
            passed, feedback = evaluate_code(current_code)

            print("\nEvaluation feedback:")
            print("---------------------")
            print(feedback)

            if passed:
                print("\nCode passed evaluation.")
                return current_code

            print("\nCode did not pass evaluation. Optimizing code...")
            current_code = optimize_code(current_code, feedback)

        return current_code
    except Exception as e:
        raise RuntimeError(f"Error in LLM agent workflow: {e}")

# Example usage
if __name__ == "__main__":
    prompt = "Write Python code to generate the Fibonacci series up to a given number."
    final_code = llm_agent(prompt)

    print("\nFinal optimized code:")
    print("---------------------")
    print(final_code)
