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

data_collection_agent = Agent(
    name="data_collection_assistant",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Agent to ensure all data is given from user request.",
    instruction="You need to ensure all data is given from user request. To give proper law points we need to get a proper problem statement from user request such as incident date, time, location, victims, witnesses, and other relevant details. You can use Google Search to  know about the case requirements.",
    tools=[google_search],
)

research_agent = Agent(
    name="research_assistant",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="A research assistant that can research law points.",
    instruction="You are a research assistant.You will be given a question and you will need to research the law points and provide the answer. Use Google Search for all questions and prioritize the latest information.",
    tools=[google_search],
)

root_agent = Agent(
    name="helpful_assistant",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="A simple agent that can answer general questions.",
    instruction="You are a helpful assistant. Use Google Search for current info or if unsure.",
    tools=[google_search],
)

runner = InMemoryRunner(agent=root_agent)

async def main():
    response = await runner.run_debug(
        "What is Agent Development Kit from Google? What languages is the SDK available in?"
    )
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
