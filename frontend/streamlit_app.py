import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the page
st.set_page_config(
    page_title="Receipt Chat Assistant",
    page_icon="🧾",
    layout="wide"
)

# API base URL
API_BASE_URL = "http://ocr:8000"  # Using Docker service name

# Get model from environment
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-2.5-flash")

st.title("🧾 Receipt Chat Assistant")

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'username' not in st.session_state:
    st.session_state.username = "streamlit_user"
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar for user settings and receipt upload
with st.sidebar:
    st.header("Settings")
    
    # Username input
    username = st.text_input("Username", value=st.session_state.username, key="username_input")
    if username != st.session_state.username:
        st.session_state.username = username
        st.session_state.session_id = None  # Reset session when user changes
        st.session_state.messages = []  # Clear chat history
    
    st.divider()
    
    # Receipt Upload Section
    st.header("📤 Upload Receipt")
    uploaded_file = st.file_uploader(
        "Choose a receipt image", 
        type=["jpg", "jpeg", "png"],
        help="Upload a receipt image for OCR processing"
    )
    
    if uploaded_file is not None:
        # Display the uploaded image
        st.image(uploaded_file, caption="Uploaded Receipt", use_column_width=True)
        
        if st.button("Process Receipt", type="primary"):
            with st.spinner("Processing receipt..."):
                try:
                    # Prepare the file for upload
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    
                    # Add username as form data
                    data = {"username": st.session_state.username}
                    
                    response = requests.post(
                        f"{API_BASE_URL}/ocr",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Receipt processed successfully!")
                        st.text_area("Extracted Text:", result.get("result", ""), height=150)
                    else:
                        st.error(f"Error processing receipt: {response.status_code}")
                        st.error(response.text)
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.divider()
    
    # Chat controls
    if st.button("🗑️ Clear Chat", help="Clear the current chat session"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

# Main chat interface
st.header("💬 Chat with Receipt Assistant")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input():
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            # Prepare the request payload
            chat_payload = {
                "message": prompt,
                "model": OPENAI_MODEL,  # Using model from environment
                "username": st.session_state.username
            }
            
            # Add session_id if we have one
            if st.session_state.session_id:
                chat_payload["session_id"] = st.session_state.session_id
            
            # Send request to chat API
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json=chat_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_response = result.get("response", "I apologize, but I couldn't process your request.")
                
                # Store the session_id for future requests
                if "session_id" in result:
                    st.session_state.session_id = result["session_id"]
                
                message_placeholder.markdown(assistant_response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
            else:
                error_message = f"Error: {response.status_code} - {response.text}"
                message_placeholder.markdown(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                
        except Exception as e:
            error_message = f"Error connecting to API: {str(e)}"
            message_placeholder.markdown(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})

# Display session info
if st.session_state.session_id:
    st.caption(f"Session ID: {st.session_state.session_id}")
st.caption(f"Username: {st.session_state.username}")
st.caption(f"Model: {OPENAI_MODEL}")