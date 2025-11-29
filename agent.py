import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool, google_search, FunctionTool
from google.genai import types
from dotenv import load_dotenv

# --- Supabase Imports ---
from supabase import create_client, Client
import uuid  # For generating a unique session ID
# ------------------------

# --- Legal BERT Tool Import ---
from legal_bert_tool import search_similar_legal_text
# -------------------------------

# Load environment variables from .env file
load_dotenv()


# Your existing ADK setup (API Key, Retry Config, Agents, Runner) goes here
# ...

# --- Supabase Configuration ---
# e.g., "https://xyz.supabase.co"
SUPABASE_URL = "https://slwakayleeoatjunvwoy.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Load from environment variable
# ------------------------------

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def check_supabase_connection(url: str, key: str) -> bool:
    """Attempts to connect to Supabase and perform a simple read operation."""
    print("Attempting to verify Supabase connection...")
    try:
        supabase: Client = create_client(url, key)

        # Attempt a simple, quick operation on the 'chat_sessions' table
        # We limit to 1 row and select only the ID to minimize bandwidth.
        response = supabase.table('chat_sessions').select(
            'id').limit(1).execute()

        # If the response is successful (no exception was raised), the connection works.
        # The structure of the result confirms connectivity and valid credentials.
        if response.data is not None:
            print("✅ Supabase connection successful! Table operations are working.")
            return True
        else:
            print("⚠️ Supabase connected, but query returned unexpected data.")
            return False

    except Exception as e:
        print(f"❌ Supabase connection failed.")
        print(f"Error details: {e}")
        return False


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)

llm_model = Gemini(
    model="gemini-2.5-flash",
    retry_options=retry_config
)

research_agent = Agent(
    name="research_assistant",
    model=llm_model,
    description="A research assistant that can research law points and analyze legal texts using InLegalBERT.",
    instruction="""You are a research assistant specialized in Indian law. You can:
    1. Research law points using google search and provide the latest legal information
    2. Analyze legal texts semantically using the InLegalBERT model (trained on Indian legal corpus)
    3. Find similarities between legal documents and queries
    
    When you find relevant legal text through search, you can use the search_similar_legal_text tool 
    to analyze it more deeply and extract the most relevant portions for the user's query.""",
    tools=[google_search, search_similar_legal_text],
    output_key="research_findings"
)

root_agent = Agent(
    name="ai_advocate",
    model=llm_model,
    description="An AI legal advocate assistant that helps users understand their rights and provides legal information.",
    instruction="""You are an AI legal advocate assistant. Your role is to:
    1. Collect all necessary information from the user (incident date, time, location, victims, witnesses, etc.)
    2. Research relevant legal information and rights using the research_agent
    3. Provide clear, helpful guidance about legal rights and options based on the research_findings
    """,
    tools=[AgentTool(agent=research_agent)],
)


def get_runner():
    """Creates a fresh runner instance for every request."""
    # We recreate the runner so it attaches to the new Streamlit event loop

    return InMemoryRunner(agent=root_agent)


async def main():
    # ... Your existing Supabase and prompt setup ...
    session_id = str(uuid.uuid4())
    user_prompt = "I got hit by a car today(2025-11-21) at 10:00 AM on Main Street and I was hit by a car driven by John Doe. I was injured and I want to know what my rights are. There are two witnesses, Jane Doe and John Smith, who saw the incident. Police report says the car was driving at 50 mph in a 30 mph zone."

    # 1. Store the User's Message (Ensure this uses the global 'supabase' client)
    # ... (omitted for brevity, but keep your user message storage here) ...

    # 2. Run the Agent
    local_runner = get_runner()
    print("Running Agent...")
    response = await local_runner.run_debug(user_prompt)

    # 3. Access the Agent's Final Output (The correct way to handle the Event list)
    advocate_response = "Agent execution completed, but final response could not be extracted."
    metadata = {}

    if response and isinstance(response, list):
        final_event = response[-1]

        # Extract the final response text
        if hasattr(final_event, 'content') and final_event.content.parts:
            advocate_response = final_event.content.parts[0].text

        # Convert all events in the response list to a JSON-serializable format (dictionary)
        # This is for the 'full_trace' metadata in Supabase
        try:
            metadata = {
                "full_trace": [e.to_dict() for e in response]
            }
        except Exception as e:
            # Fallback if to_dict() fails for some reason
            metadata = {"full_trace_error": str(
                e), "raw_response_type": str(type(response))}

        # 4. Store the Advocate's Response (Supabase logic)
        try:
            # Use the extracted text and serializable metadata
            supabase.table('chat_sessions').insert({
                "session_id": session_id,
                "role": "advocate",
                "content": advocate_response,
                "metadata": metadata
            }).execute()
            print(
                f"✅ Advocate response saved to Supabase session: {session_id}")
        except Exception as e:
            print(f"❌ Error saving advocate response to Supabase: {e}")

        # 5. Print the final response only if you want it printed again
        print("\n--- Final Agent Response (Printed from extracted content) ---")
        print(advocate_response)

    else:
        # This block will now rarely execute if the runner succeeds
        print("Error: Agent runner returned an unexpected or empty result.")
        print(f"Raw Response: {response}")

# ... (rest of your script)

if __name__ == "__main__":
    asyncio.run(main())
