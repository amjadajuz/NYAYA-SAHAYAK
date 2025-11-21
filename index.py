import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search
from google.genai import types

GOOGLE_API_KEY = "AIzaSyCwnyYWonWTPjJPmDByVhKeLqG6Kl4FVBw"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
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
    2. Research relevant legal information and rights using Google Search
    3. Provide clear, helpful guidance about legal rights and options
    
    Always use Google Search to find the most current and relevant legal information.
    Be empathetic and professional in your responses.""",
    tools=[google_search],
)

runner = InMemoryRunner(agent=root_agent)

async def main():
    response = await runner.run_debug(
        "I got hit by a car and I want to know what my rights are."
    )
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
