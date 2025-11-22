import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool, google_search
from google.genai import types

# --- Supabase Imports ---
from supabase import create_client, Client
import uuid  # For generating a unique session ID
# ------------------------

# Your existing ADK setup (API Key, Retry Config, Agents, Runner) goes here
# ...

# --- Supabase Configuration ---
# e.g., "https://xyz.supabase.co"
SUPABASE_URL = "https://slwakayleeoatjunvwoy.supabase.co"
SUPABASE_KEY = "sb_publishable_ibch9WmO4qC3m74tyKtBkg_MfH4Y75Q"  # e.g., "eyJhbGciOi..."
# ------------------------------

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ... (Existing Agent and Runner definitions) ...

# Assuming your setup remains the same:
# research_agent = Agent(...)
# root_agent = Agent(...)
# runner = InMemoryRunner(agent=root_agent)

GOOGLE_API_KEY = "AIzaSyCwnyYWonWTPjJPmDByVhKeLqG6Kl4FVBw"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)

research_agent = Agent(
    name="research_assistant",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="A research assistant that can research law points.",
    instruction="You are a research assistant. You will be given a question and you will need to research the law points using google search and provide the answer. Prioritize the latest legal information.",
    tools=[google_search],
    output_key="research_findings"
)

root_agent = Agent(
    name="ai_advocate",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="An AI legal advocate assistant that helps users understand their rights and provides legal information.",
    instruction="""You are an AI legal advocate assistant. Your role is to:
    1. Collect all necessary information from the user (incident date, time, location, victims, witnesses, etc.)
    2. Research relevant legal information and rights using the research_agent
    3. Provide clear, helpful guidance about legal rights and options based on the research_findings
    """,
    tools=[AgentTool(agent=research_agent)],
)

runner = InMemoryRunner(agent=root_agent)


async def main():
    # 1. Generate a unique session ID for this conversation
    session_id = str(uuid.uuid4())

    user_prompt = "I got hit by a car today(2025-11-21) at 10:00 AM on Main Street and I was hit by a car driven by John Doe. I was injured and I want to know what my rights are. There are two witnesses, Jane Doe and John Smith, who saw the incident. Police report says the car was driving at 50 mph in a 30 mph zone."

    # 2. Store the User's Message
    try:
        supabase.table('chat_sessions').insert({
            "session_id": session_id,
            "role": "user",
            "content": user_prompt,
            "metadata": {}
        }).execute()
        print(f"User message saved to session: {session_id}")
    except Exception as e:
        print(f"Error saving user message to Supabase: {e}")

    # 3. Run the Agent
    print("Running Agent...")
    response = await runner.run_debug(user_prompt)

    # 4. Store the Agent's Response
    advocate_response = response.get('research_findings', str(
        response))  # Adjust key based on final output structure

    # Extract metadata like the full trace or agent's thought process if needed
    metadata = {
        "full_trace": response  # Storing the entire run_debug output for rich context
    }

    try:
        supabase.table('chat_sessions').insert({
            "session_id": session_id,
            "role": "advocate",
            "content": advocate_response,
            "metadata": metadata
        }).execute()
        print(f"Advocate response saved to session: {session_id}")
    except Exception as e:
        print(f"Error saving advocate response to Supabase: {e}")

    # 5. Print the final response
    print("\n--- Final Agent Response ---")

if __name__ == "__main__":
    asyncio.run(main())
