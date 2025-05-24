import streamlit as st
import requests
import os
import fitz  # PyMuPDF


# --- Configuration ---


API_KEY = GEMINI_API_KEY
# --- CONFIGURATION ---
GEMINI_MODEL = "gemini-2.0-flash"  # Change here: "gemini-pro" or "gemini-2.0-flash"

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent"



if not API_KEY:
    st.warning("⚠️ Please set the GEMINI_API_KEY environment variable or add it to .streamlit/secrets.toml")
    st.stop()

# --- Title and Layout ---
st.set_page_config(page_title="Gemini Chat", layout="wide")
st.title("💬 Gemini 2 Chat with File Upload and Memory")

# --- Persistent Chat State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# --- File Upload and Text Extraction ---
uploaded_files = st.file_uploader("Upload PDFs or TXT files", accept_multiple_files=True, type=["pdf", "txt"])

def extract_text_from_files(files):
    extracted = []
    for file in files:
        if file.size > 1_000_000:
            st.error(f"{file.name} is too large. Max size is 1MB.")
            continue
        if file.type == "application/pdf":
            try:
                doc = fitz.open(stream=file.read(), filetype="pdf")
                text = "\n".join([page.get_text() for page in doc])
                extracted.append(f"\n---\nExtracted from {file.name}:\n{text}")
            except Exception as e:
                st.error(f"Failed to read {file.name}: {e}")
        elif file.type == "text/plain":
            try:
                text = file.read().decode("utf-8")
                extracted.append(f"\n---\nContents of {file.name}:\n{text}")
            except Exception as e:
                st.error(f"Error reading {file.name}: {e}")
    return extracted

# --- Show Chat History ---
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# --- User Input ---
user_input = st.chat_input("Type your message here...")

def call_gemini_api(prompt):
    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}
    data = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=data)

    if response.status_code != 200:
        st.error(f"❌ API Error: {response.status_code}")
        st.text(response.text)
        return "❌ Failed to get valid response from Gemini."

    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"❌ Failed to parse Gemini response: {e}"


# --- On User Message ---
if user_input:
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Gemini is thinking..."):
            file_texts = extract_text_from_files(uploaded_files)
            full_prompt = user_input + "\n" + "\n".join(file_texts)
            gemini_reply = call_gemini_api(full_prompt)
            st.markdown(gemini_reply)
            st.session_state.chat_history.append(("assistant", gemini_reply))
