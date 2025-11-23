import streamlit as st
import asyncio
import uuid
import json

# Import your existing setup
# Ensure your agent file is named 'agent.py'
from agent import runner, supabase

st.set_page_config(page_title="Nyaya Sahayak AI", layout="wide")

st.title("⚖️ Nyaya Sahayak: AI Legal Advocate")
st.caption("Powered by Google Gemini & InLegalBERT")

# Initialize Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize Session ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "trace" in message and message["trace"]:
            with st.expander("🛠️ View Agent Trace (Debug)"):
                st.json(message["trace"])

# Handling User Input
if prompt := st.chat_input("Describe your legal situation..."):
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Run Agent (Async Wrapper)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown(
            "⏳ *Analyzing legal precedents and researching...*")

        try:
            # We use asyncio.run to execute the async ADK runner within Streamlit
            response = asyncio.run(runner.run_debug(prompt))

            # 3. Extract Response & Trace
            advocate_response = "I couldn't generate a response."
            full_trace = []

            if response and isinstance(response, list):
                final_event = response[-1]
                # Extract text
                if hasattr(final_event, 'content') and final_event.content.parts:
                    advocate_response = final_event.content.parts[0].text

                # Extract trace for debugging
                try:
                    full_trace = [e.to_dict() for e in response]
                except:
                    full_trace = ["Could not serialize trace"]

            # 4. Display Assistant Response
            message_placeholder.markdown(advocate_response)

            if full_trace:
                with st.expander("🛠️ View Agent Trace (Debug)"):
                    st.json(full_trace)

            # 5. Save to Supabase (Preserving your logic)
            if supabase:
                try:
                    metadata = {"full_trace": full_trace}
                    supabase.table('chat_sessions').insert({
                        "session_id": st.session_state.session_id,
                        "role": "advocate",
                        "content": advocate_response,
                        "metadata": metadata
                    }).execute()
                    # Optional: Show a small success toast
                    st.toast(f"✅ Saved to Supabase", icon="💾")
                except Exception as e:
                    st.error(f"❌ Failed to save to Supabase: {e}")

            # Update Chat History
            st.session_state.messages.append({
                "role": "assistant",
                "content": advocate_response,
                "trace": full_trace
            })

        except Exception as e:
            st.error(f"An error occurred: {e}")
