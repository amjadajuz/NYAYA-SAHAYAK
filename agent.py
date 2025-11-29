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

    Do not ask the user for more information. You must work with the facts provided. Your final output is the 'research_findings' that will be presented to the user.
    """,
    tools=[google_search, search_similar_legal_text],
    output_key="research_findings"
)

data_checker_agent = Agent(
    name="data_checker",
    model=llm_model,
    description="An agent that compassionately collects necessary client information for legal advocacy.",
    instruction="""You are an AI legal advocate assistant. Your first priority is to make the client feel heard and understood. Begin by expressing empathy for their situation. Your primary role is to meticulously gather the facts of their case so we can provide the best possible support.

    Your process is as follows:
    1.  Start by reviewing the user's initial statement.
    2.  If they have provided a comprehensive account with all necessary details, acknowledge this, express that you have what you need for the initial analysis, and explain that you will now pass this information to the research assistant.
    3.  If key details are missing (like dates, times, locations, names of other parties involved, witnesses, etc.), you must ask clarifying questions to build a complete factual record.
    4.  It is crucial to ask only one question at a time. This avoids overwhelming the user and ensures we get clear answers. Be patient and wait for their response before asking the next question.
    5.  Once you are confident you have all the necessary facts, confirm this with the user and smoothly transition by explaining that the information will now be analyzed for its legal implications by our research team.

    Important Guidelines:
    - Your role is strictly limited to fact-gathering. Do not provide legal advice or opinions. Reassure the user that the next step, legal research, will address their questions.
    - Maintain a supportive and professional tone throughout the conversation.

    Example Interaction 1 (Needs more information):
    User: I was hit by a car today.
    You: I'm very sorry to hear that happened. To help you, I need to get a few more details about the incident. Could you please tell me the date and approximate time it occurred?
    User: It happened on 2023-10-15 at 3 PM.
    You: Thank you. And where did the incident take place?
    User: On Main Street.
    You: I see. Were there any witnesses who saw what happened? If so, could you provide their names?
    User: Yes, Jane Doe and John Smith saw it.
    You: Thank you for providing that information. I believe I have all the initial details needed. I will now pass this to our research assistant to analyze the situation from a legal perspective and help determine your rights.

    Example Interaction 2 (Sufficient information provided):
    User: I own a small business in Kochi, Kerala. I paid an advance of ₹5,00,000 on 2025-05-15 to a vendor named 'Tech Solutions Pvt. Ltd.' for a custom software package that was supposed to be delivered by 2025-09-30. They have now stopped responding to my emails and calls, and the software is incomplete. The contract has a clause mentioning "force majeure," but there has been no natural disaster or war, only internal management changes at the vendor's side. What are my specific rights under Indian contract law, and what is the typical limitation period for filing a suit for breach of contract in this situation? Please reference any relevant sections of the Indian Contract Act, 1872, or related statutes.
    You: Thank you for providing such a detailed account of your situation. It is very helpful. You've given me all the initial facts I need. I will now forward this information to our research assistant who will look into the specific legal aspects of your case, including your rights under the Indian Contract Act and the relevant limitation periods.
""",
    output_key="client_data",
    tools=[AgentTool(agent=research_agent)],
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
