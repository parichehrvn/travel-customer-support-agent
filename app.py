import uuid

from travel_agent.core.rag_pipeline import run_rag
import streamlit as st


thread_id = str(uuid.uuid4())


def get_response(question):
    passenger_id = st.session_state["passenger_id"]
    return run_rag(passenger_id, thread_id, question)


st.set_page_config(
    page_icon="✈️",
    page_title="Swiss Airline Assistant",
    layout="centered",
)


# --- Initialize session state ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["passenger_id"] = None

if "messages" not in st.session_state:
    st.session_state["messages"] = []


# --- Login Page ---
def login_page():
    st.title("✈️ Airline Assistant - Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        # 🔹 Fake check: replace with DB or API lookup
        if username == "demo" and password == "1234":
            st.session_state["logged_in"] = True
            st.session_state["passenger_id"] = "3442 587242"
            st.rerun()  # reload app -> go to chat page
        else:
            st.error("Invalid username or password")


def chat_page():
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem;">
            <h1>Your Personal Airline Assistant</h1>
            <p style="color: gray;">Ask about flights, hotels, or get travel recommendations.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Initial Greeting
    if not st.session_state["messages"]:
        st.session_state["messages"].append({
            "role": "Assistant",
            "content": "👋 Hi! I’m your Airline Assistant. How can I help with your trip today?"
        })

    with st.container():
        for msg in st.session_state["messages"]:
            avatar = "🧑" if msg["role"] == "user" else "🤖"
            st.chat_message(msg["role"], avatar=avatar).markdown(msg["content"])

    question = st.chat_input("Ask about flights, hotels, or get travel recommendations.")

    if question:
        st.session_state["messages"].append({"role": "user", "content": question})
        st.chat_message("user", avatar="🧑").markdown(f"**{question}**")

        with st.chat_message("Assistant", avatar="🤖"):
            placeholder = st.empty()
            st.session_state["messages"].append({"role": "Assistant", "content": ""})
            idx = len(st.session_state["messages"]) - 1

            full_response = ""

            with st.spinner('Thinking...⌛'):
                for chunk in get_response(question):  # yields chunks
                    full_response += chunk
                    st.session_state["messages"][idx]["content"] = full_response  # persist partials
                    placeholder.markdown(full_response)



# --- App flow controller ---
if not st.session_state["logged_in"]:
    login_page()
else:
    chat_page()