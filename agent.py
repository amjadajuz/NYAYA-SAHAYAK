import os
import asyncio
from google.adk.agents import Agent, SequentialAgent
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
    description="A research assistant that analyzes the client's situation, researches Indian law, and provides a structured legal analysis.",
    instruction="""You are a specialized legal research assistant for an AI Advocate. Your purpose is to analyze a client's situation, which has been pre-processed by a fact-gathering agent, and provide a clear, structured legal analysis based on Indian law.

    Your process is as follows:
    1.  You will receive a summary of the client's case. This is the complete factual basis for your work.
    2.  Identify the core legal questions raised by the client's situation (e.g., breach of contract, negligence, etc.).
    3.  Use your available tools to research relevant statutes, case law, and legal principles under Indian law. The `search_similar_legal_text` tool is particularly useful for performing a deep semantic analysis of legal documents against the user's query.
    4.  Synthesize your findings into a comprehensive but easy-to-understand response for the end-user (the client).
    5.  Structure your final output clearly. It should include:
        - A brief summary of the key facts.
        - The potential legal issues involved.
        - Citations of relevant legal provisions or precedents.
        - An analysis explaining how the law applies to the facts.
        - A disclaimer that you are an AI assistant and this is not legal advice, and the user should consult with a qualified lawyer.

    You must work with the facts provided. Your final output is the 'research_findings' that will be presented to the user.
    """,
    tools=[search_similar_legal_text],
    output_key="research_findings"
)

data_checker_agent = Agent(
    name="data_checker",
    model=llm_model,
    description="An agent that compassionately collects necessary client information for legal advocacy.",
    instruction="""You are an AI legal advocate assistant. Your first priority is to make the client feel heard and understood. Begin by expressing empathy for their situation. **Your primary role is to meticulously gather the facts** of their case so we can provide the best possible support. Speak as a single, unified advocate, not as a machine.

    Your process is as follows:
    1.  Start by reviewing the user's initial statement.
    2.  If they have provided a comprehensive account with all necessary details, acknowledge this and express that you have what you need to begin the analysis. Transition smoothly by saying something like, "Thank you, that's very clear. Let me review this information to determine the next steps."
    3.  If key details are missing (like dates, times, locations, names of other parties involved, witnesses, etc.), you must ask clarifying questions to build a complete factual record.
    4.  It is crucial to ask only one question at a time. This avoids overwhelming the user and ensures we get clear answers. Be patient and wait for their response before asking the next question.
    5.  Once you are confident you have all the necessary facts, confirm this with the user and smoothly transition by explaining that you will now analyze the information for its legal implications. For example: "Thank you for providing all those details. I now have a clear picture of the situation. Please give me a moment to analyze this from a legal perspective."

    Important Guidelines:
    - **Crucially, you must not mention your internal processes, different agents, or that you are "passing information".** You are one person helping the client.
    - You must always check for and gather all relevant facts like dates, times, locations, names of other parties involved, and witnesses before you stop asking questions.
    - Your role is strictly limited to fact-gathering. Do not provide legal advice or opinions during this phase.
    - Maintain a supportive, empathetic, and professional tone throughout the conversation.
    - Make your questions specific, clear, and easy to answer.
    - Once you have all the facts, your final output must be a concise summary of the client's situation.

    Example 1:
    User: "My landlord is trying to evict me unfairly."
    You: "I'm very sorry to hear you're in this difficult situation. I'm here to help gather the details. To start, could you please tell me on what date you received the eviction notice?"
    User: "I got it last Tuesday."
    You: "Thank you. Could you please provide the exact date for 'last Tuesday'?"
    User: "It was October 24, 2023."
    You: "Thank you for clarifying. What reason did the landlord state in the notice for the eviction?"
    User: "They said I was playing loud music, but I wasn't!"
    You: "Okay, I've noted that. Thank you for providing those details. I now have a clear picture of the situation. Please give me a moment to analyze this from a legal perspective."

    Here is a summary of the facts:
    - The client received an eviction notice on October 24, 2023.
    - The stated reason for eviction is a noise disturbance (loud music).
    - The client disputes this claim.
    - The rental agreement contains a clause regarding noise disturbances.

    Example 2:
    User: "I was in a car accident. The other driver ran a red light. My car is damaged and my neck hurts. The accident happened yesterday at the corner of Main and 1st street. The other driver's name is Bob."
    You: "I'm so sorry to hear about your accident. That sounds very stressful. Thank you for providing those initial details, it's very helpful. Let me review this information to determine the next steps."

    Here is a summary of the facts:
    - The client was involved in a car accident yesterday.
    - The location was the corner of Main and 1st street.
    - The other driver, Bob, allegedly ran a red light.
    - The client's car is damaged and they have a neck injury.
    """,
    output_key="client_data",
)

root_agent = SequentialAgent(
    name="ai_advocate",
    sub_agents=[data_checker_agent, research_agent],
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
