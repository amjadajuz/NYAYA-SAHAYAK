from agent import get_runner, supabase
import streamlit as st
import asyncio
import uuid
import nest_asyncio

# 1. APPLY THE PATCH IMMEDIATELY
nest_asyncio.apply()

# 2. Import the FUNCTION, not the runner variable
# Ensure agent.py has the get_runner function we created in Step 1

st.set_page_config(page_title="Nyaya Sahayak AI", layout="wide")
st.title("⚖️ Nyaya Sahayak: AI Legal Advocate")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "trace" in message and message["trace"]:
            with st.expander("🛠️ View Agent Trace"):
                st.json(message["trace"])

if prompt := st.chat_input("Describe your legal situation..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ *Analyzing...*")

        try:
            # 3. GET A FRESH RUNNER INSTANCE
            # This creates the runner inside the current active loop
            current_runner = get_runner()

            # 4. RUN STANDARD ASYNCIO
            # Because we have nest_asyncio applied and a fresh runner,
            # simple asyncio.run() works best now.
            response = asyncio.run(current_runner.run_debug(prompt))

            # Extract Response
            advocate_response = "I couldn't generate a response."
            full_trace = []

            if response and isinstance(response, list):
                final_event = response[-1]
                if hasattr(final_event, 'content') and final_event.content.parts:
                    advocate_response = final_event.content.parts[0].text
                try:
                    full_trace = [e.to_dict() for e in response]
                except:
                    full_trace = ["Trace Error"]

            placeholder.markdown(advocate_response)

            if full_trace:
                with st.expander("🛠️ View Agent Trace"):
                    st.json(full_trace)

            # Save to Supabase
            if supabase:
                try:
                    supabase.table('chat_sessions').insert({
                        "session_id": st.session_state.session_id,
                        "role": "advocate",
                        "content": advocate_response,
                        "metadata": {"full_trace": full_trace}
                    }).execute()
                except Exception as db_e:
                    print(f"DB Error: {db_e}")

            st.session_state.messages.append({
                "role": "assistant",
                "content": advocate_response,
                "trace": full_trace
            })

        except Exception as e:
            st.error(f"Error: {e}")
