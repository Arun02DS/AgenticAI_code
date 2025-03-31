import streamlit as st
import requests

# Flask API endpoint
API_URL = "http://127.0.0.1:5000/process"

def get_next_question(user_input, question):
    """Send user input to the backend and get the next question."""
    response = requests.post(API_URL, json={"user_input": user_input, "question": question})
    if response.status_code == 200:
        return response.json().get("next_question", "Error: No response from server.")
    return "Error: Could not fetch response."

# Streamlit UI setup
st.title("🗣️ AI Interview Chatbot")
st.write("This chatbot simulates an interview. Respond to the questions, and the AI will evaluate and continue the conversation.")

# Session state to maintain chat history and current question
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [("bot", "Tell me about yourself.")]
    st.session_state.current_question = "Tell me about yourself."

# Display chat history
for sender, message in st.session_state.chat_history:
    with st.chat_message("assistant" if sender == "bot" else "user"):
        st.write(message)

# User input field
user_input = st.chat_input("Your response...")
if user_input:
    # Append user input to chat history
    st.session_state.chat_history.append(("user", user_input))
    
    # Fetch next question from API
    next_question = get_next_question(user_input, st.session_state.current_question)
    
    # Append the bot's next question to chat history
    st.session_state.chat_history.append(("bot", next_question))
    
    # Update current question to the new one
    st.session_state.current_question = next_question
    
    # Rerun to update chat display
    st.rerun()
