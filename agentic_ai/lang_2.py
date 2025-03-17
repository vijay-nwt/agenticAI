from typing import TypedDict
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
import asyncio
import os
from dotenv import load_dotenv

# Define schema for agent state
class AgentState(TypedDict):
    query: str
    response: str

# Load environment variables
load_dotenv()

# Get API keys from environment
API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not API_KEY:
    raise ValueError("Missing OpenAI API Key. Ensure it's set in the .env file.")

# OpenAI Client
gpt_model_client = ChatOpenAI(
    model_name="gpt-4o-mini",
    openai_api_key=API_KEY
)

# Define the router function
def router(state: AgentState) -> AgentState:
    user_query = state["query"]
    response = gpt_model_client.invoke(user_query)
    return {"query": user_query, "response": response}

# Initialize StateGraph with the schema
workflow = StateGraph(AgentState)

# Add the router node
workflow.add_node("router", router)

# Set the entry point
workflow.set_entry_point("router")

# Compile the graph
executor = workflow.compile()

async def main():
    while True:
        user_input = input("You: ")  
        if user_input.lower() == "exit":
            print("Thank you for using the system. Goodbye!")
            break
        result = executor.invoke({"query": user_input})  # Execute workflow
        print("AI Response:", result["response"])

if __name__ == "__main__":
    asyncio.run(main())
