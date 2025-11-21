import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool, google_search
from google.genai import types

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
    response = await runner.run_debug(
        "I got hit by a car today(2025-11-21) at 10:00 AM on Main Street and I was hit by a car driven by John Doe. I was injured and I want to know what my rights are. There are two witnesses, Jane Doe and John Smith, who saw the incident. Police report says the car was driving at 50 mph in a 30 mph zone."
    )
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
