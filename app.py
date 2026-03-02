import streamlit as st
import requests
import uuid
import json
import os

# ---------- CONFIG ----------
SESSION_DIR = "sessions"

if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

# ---------- FUNCTIONS ----------

def session_file(session_id):
    return os.path.join(SESSION_DIR, f"{session_id}.json")


def save_session(session_id):

    data = {
        "name": st.session_state.session_names[session_id],
        "messages": st.session_state.sessions[session_id]
    }

    with open(session_file(session_id), "w") as f:
        json.dump(data, f, indent=2)


def load_sessions():

    sessions = {}
    names = {}

    for file in os.listdir(SESSION_DIR):

        if file.endswith(".json"):

            session_id = file.replace(".json", "")

            with open(session_file(session_id), "r") as f:

                data = json.load(f)

                sessions[session_id] = data.get("messages", [])
                names[session_id] = data.get("name", "New Chat")

    return sessions, names


def create_new_session():

    new_id = str(uuid.uuid4())

    st.session_state.sessions[new_id] = []
    st.session_state.session_names[new_id] = "New Chat"

    save_session(new_id)

    st.session_state.current_session = new_id


# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="DeepScan AI",
    page_icon="🧠",
    layout="wide"
)

# ---------- CUSTOM UI ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #000000, #1a1a1a, #2b2b2b);
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ---------- INIT STATE ----------
if "sessions" not in st.session_state:

    sessions, names = load_sessions()

    st.session_state.sessions = sessions
    st.session_state.session_names = names

if "current_session" not in st.session_state:

    if st.session_state.sessions:

        st.session_state.current_session = list(
            st.session_state.sessions.keys())[0]

    else:

        create_new_session()

# ---------- SIDEBAR ----------
with st.sidebar:

    st.markdown("## 🧠 DeepScan AI")

    # New Chat
    if st.button("➕ New Chat"):

        create_new_session()

        st.rerun()

    st.markdown("---")
    st.markdown("### Chats")

    for session_id in list(st.session_state.sessions.keys()):

        col1, col2, col3 = st.columns([6,1,1])

        # Select chat
        with col1:

            if st.button(
                st.session_state.session_names[session_id],
                key=f"select_{session_id}"
            ):

                st.session_state.current_session = session_id

                st.rerun()

        # Rename chat
        with col2:

            if st.button("✏️", key=f"rename_{session_id}"):

                st.session_state.rename_target = session_id

        # Delete chat
        with col3:

            if st.button("🗑", key=f"delete_{session_id}"):

                st.session_state.delete_target = session_id
                st.session_state.confirm_delete = True

    # Rename UI
    if "rename_target" in st.session_state:

        st.markdown("---")

        new_name = st.text_input(
            "Rename chat:",
            value=st.session_state.session_names[
                st.session_state.rename_target
            ]
        )

        colA, colB = st.columns(2)

        with colA:

            if st.button("Save"):

                sid = st.session_state.rename_target

                st.session_state.session_names[sid] = new_name

                save_session(sid)

                del st.session_state.rename_target

                st.rerun()

        with colB:

            if st.button("Cancel"):

                del st.session_state.rename_target

                st.rerun()

    # Delete confirmation
    if st.session_state.get("confirm_delete", False):

        st.error(
            "This chat will be permanently deleted. This action cannot be undone."
        )

        colA, colB = st.columns(2)

        # Proceed
        with colA:

            if st.button("Proceed", type="primary"):

                sid = st.session_state.delete_target

                os.remove(session_file(sid))

                del st.session_state.sessions[sid]
                del st.session_state.session_names[sid]

                if st.session_state.sessions:

                    st.session_state.current_session = list(
                        st.session_state.sessions.keys())[0]

                else:

                    create_new_session()

                del st.session_state.delete_target
                del st.session_state.confirm_delete

                st.rerun()

        # Cancel
        with colB:

            if st.button("Cancel"):

                del st.session_state.delete_target
                del st.session_state.confirm_delete

                st.rerun()

# ---------- MAIN ----------
st.title("DeepScan AI")

# Upload PDF
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:

    files = {"file": uploaded_file.getvalue()}

    requests.post(
        "http://localhost:8000/upload",
        files=files
    )

    st.success("PDF uploaded successfully")

# ---------- CHAT ----------
session_id = st.session_state.current_session

chat_history = st.session_state.sessions[session_id]

# Display history
for msg in chat_history:

    st.chat_message(msg["role"]).write(msg["content"])

# Chat input
question = st.chat_input("Ask DeepScan AI...")

if question:

    # Save user message
    chat_history.append({
        "role": "user",
        "content": question
    })

    # Auto name
    if len(chat_history) == 1:

        st.session_state.session_names[session_id] = question[:40]

    save_session(session_id)

    st.chat_message("user").write(question)

    # Call backend
    response = requests.post(
        "http://localhost:8000/query",
        json={"question": question}
    )

    answer = response.json()["answer"]

    chat_history.append({
        "role": "assistant",
        "content": answer
    })

    save_session(session_id)

    st.chat_message("assistant").write(answer)