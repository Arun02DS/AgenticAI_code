from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.output_parsers import StrOutputParser
import re
from typing import Optional, Dict
from typing_extensions import TypedDict

# Load environment variables
load_dotenv()

# Define constants
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# Initialize Azure OpenAI model
try:
    model = AzureChatOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        deployment_name=AZURE_OPENAI_DEPLOYMENT_NAME,
        openai_api_key=AZURE_OPENAI_API_KEY,
        openai_api_version="2024-08-01-preview",
    )
except Exception as e:
    print(f"Error initializing Azure OpenAI model: {e}")
    exit(1)

# Define TypedDict for state management
class QuestionFlowState(TypedDict):
    user_input: str
    question: Optional[str]
    score: Optional[int]
    next_question: Optional[str]

# Define prompt templates
QUESTION_PROMPT = PromptTemplate(
    input_variables=["user_input"],
    template="Generate a relevant question based on the user input: {user_input}"
)

EVALUATION_PROMPT = PromptTemplate(
    input_variables=["user_input", "question"],
    template=("Evaluate the user input: {user_input} against the question: {question}. "
              "Provide a score from 1 to 10 based on relevance and correctness.")
)

NEXT_QUESTION_PROMPT_EASIER = PromptTemplate(
    input_variables=["score", "user_input"],
    template="User scored {score}. Generate an easier question related to: {user_input}"
)

NEXT_QUESTION_PROMPT_HARDER = PromptTemplate(
    input_variables=["score", "user_input"],
    template="User scored {score}. Generate a more challenging question related to: {user_input}"
)

# Define LLM chains
generate_question_chain = LLMChain(llm=model, prompt=QUESTION_PROMPT, output_parser=StrOutputParser())
evaluate_answer_chain = LLMChain(llm=model, prompt=EVALUATION_PROMPT, output_parser=StrOutputParser())

def generate_question(inputs: Dict[str, str]) -> Dict[str, str]:
    """Generate a question based on user input"""
    response = generate_question_chain.invoke({"user_input": inputs.get("user_input", "None")})
    return {"question": response} if isinstance(response, str) else {"question": str(response)}

def evaluate_answer(inputs: Dict[str, str]) -> Dict[str, int]:
    """Evaluate the user's response and return a score"""
    response = evaluate_answer_chain.invoke({"user_input": inputs.get("user_input", ""), "question": inputs.get("question", "")})

    # Ensure response is a string before applying regex
    response_text = response if isinstance(response, str) else str(response)
    match = re.search(r"\b(\d+)\b(?:\s*out of\s*10|\s*/\s*10|\s*\/10)?", response_text, re.IGNORECASE)

    score = int(match.group(1)) if match else 0
    return {"score": score}

def generate_next_question(inputs: Dict[str, str]) -> Dict[str, str]:
    """Generate the next question based on the user's score"""
    score = inputs.get("score", 0)

    if score < 5:
        next_question_chain = LLMChain(llm=model, prompt=NEXT_QUESTION_PROMPT_EASIER, output_parser=StrOutputParser())
    else:
        next_question_chain = LLMChain(llm=model, prompt=NEXT_QUESTION_PROMPT_HARDER, output_parser=StrOutputParser())

    response = next_question_chain.invoke({"score": score, "user_input": inputs.get("user_input", "")})
    return {"next_question": response} if isinstance(response, str) else {"next_question": str(response)}

def process_flow(inputs: Dict[str, str]) -> Dict[str, str]:
    """Process the user's input and generate the next question"""
    if inputs["user_input"].lower() in ["exit", "quit"]:
        return {"next_question": "Thank you for participating!"}

    question_result = generate_question(inputs)
    inputs.update(question_result)

    score_result = evaluate_answer(inputs)
    inputs.update(score_result)

    next_question_result = generate_next_question(inputs)
    inputs.update(next_question_result)

    return inputs

# Build LangGraph
graph = StateGraph(QuestionFlowState)
graph.add_node("process_flow", process_flow)
graph.add_edge(START, "process_flow")
graph.add_edge("process_flow", END)
app_graph = graph.compile()

# Initialize Flask app
app = Flask(__name__)

@app.route("/process", methods=["POST"])
def process():
    data = request.json
    user_input = data.get("user_input", "")
    previous_question = data.get("question", "")

    response = app_graph.invoke({"user_input": user_input, "question": previous_question})

    # Extract text field from response if it exists
    next_question_text = response.get("next_question", {})
    
    if isinstance(next_question_text, dict) and "text" in next_question_text:
        next_question_text = next_question_text["text"]

    return jsonify({
        "next_question": next_question_text
    })

if __name__ == "__main__":
    app.run(debug=True)

