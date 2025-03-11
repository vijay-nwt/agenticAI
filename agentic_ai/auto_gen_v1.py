from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import AgentEvent, ChatMessage
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

# Define external tools/functions that agents can use
async def get_account_balance(account_id: str) -> str:
    """Retrieve the current balance for a given account ID."""
    # In a real implementation, this would query a database or API
    # Mock implementation for demonstration
    balances = {
        "ACC123": "$542.50",
        "ACC456": "$1,205.75",
        "ACC789": "$0.00"
    }
    return balances.get(account_id, "Account not found")

async def check_service_status(service_type: str) -> str:
    """Check the current status of a service (internet, phone, cable)."""
    # Mock implementation
    statuses = {
        "internet": "All systems operational",
        "phone": "Experiencing outages in the Northeast region",
        "cable": "Maintenance scheduled for tonight 2-4am"
    }
    return statuses.get(service_type.lower(), "Unknown service type")

async def search_product_catalog(query: str) -> str:
    """Search the product catalog for items matching the query."""
    # Mock implementation
    if "phone" in query.lower():
        return "Found 15 phone models in our catalog. Top results: iPhone 15, Samsung Galaxy S23, Google Pixel 8"
    elif "internet" in query.lower():
        return "Found 5 internet plans: Basic (25Mbps), Standard (100Mbps), Premium (500Mbps), Ultra (1Gbps), Business (2Gbps)"
    else:
        return f"No exact matches for '{query}'. Try broadening your search terms."

async def check_flight_availability(destination: str, date: str) -> str:
    """Check flight availability to a destination on a specific date."""
    # Mock implementation
    return f"Found 8 flights to {destination} on {date}. Prices range from $299 to $750."

# Create function tools
account_balance_tool = FunctionTool(get_account_balance, description="Get account balance by ID")
service_status_tool = FunctionTool(check_service_status, description="Check service status")
product_search_tool = FunctionTool(search_product_catalog, description="Search product catalog")
flight_tool = FunctionTool(check_flight_availability, description="Check flight availability")

# OpenAI Client
gpt_model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key=API_KEY
)

# Routing Agent - Determines the required module
RoutingAgent = AssistantAgent(
    "PlanningAgent",
    description="An agent for planning tasks, this agent should be the first to engage when given a new task.",
    model_client=gpt_model_client,
    system_message="""
    You are a planing agent. Your job is to identify the intent of the user and delegate the request to the correct agent.
     You only plan and delegate tasks - you do not execute them yourself. 
     The available agents are:
        - TechSupportAgent: For troubleshooting internet, phone, cable, or software installation.
        - AccountsBillingAgent: For account balances, plan upgrades, and payments.
        - ConversationalSearchAgent: For FAQs, product availability, and catalog filtering.
        - TravelConciergeAgent: For booking flights, hotels, and travel-related queries.
        - FrontDeskAgent: For handling appointments, service inquiries, and call transfers.
     You can engage with agnets multiple times

    When assigning tasks, use this format:
    1. <agent> : <task>
    Note: if you don't find relevant information, just say "No relevant information found"
    After all tasks are complete, summarize the findings and end with "TERMINATE".
    
    """
)

# Tech Support Agent with tools
TechSupportAgent = AssistantAgent(
    "TechSupportAgent",
    model_client=gpt_model_client,
    system_message="""
    You handle technical support issues such as troubleshooting, device setup, and software installation.
    You have access to tools that can check service status. Use these tools to provide accurate information.
    """,
    tools=[service_status_tool]
)

# Accounts and Billing Agent with tools
AccountsBillingAgent = AssistantAgent(
    "AccountsBillingAgent",
    model_client=gpt_model_client,
    system_message="""
    You manage account details, billing, plan upgrades, and payments.
    You have access to tools that can check account balances. Use these tools to provide accurate information.
    """,
    tools=[account_balance_tool]
)

# Conversational Search Agent with tools
ConversationalSearchAgent = AssistantAgent(
    "ConversationalSearchAgent",
    model_client=gpt_model_client,
    system_message="""
    You search FAQs, knowledge bases, and product availability.
    You have access to tools that can search the product catalog. Use these tools to provide accurate information.
    """,
    tools=[product_search_tool]
)

# Travel Concierge Agent with tools
TravelConciergeAgent = AssistantAgent(
    "TravelConciergeAgent",
    model_client=gpt_model_client,
    system_message="""
    You assist users with travel bookings, comparisons, and recommendations.
    You have access to tools that can check flight availability. Use these tools to provide accurate information.
    """,
    tools=[flight_tool]
)

# Front Desk Agent
FrontDeskAgent = AssistantAgent(
    "FrontDeskAgent",
    model_client=gpt_model_client,
    system_message="You handle appointment bookings, business hours, and general inquiries."
)

# Termination Conditions
text_mention_termination = TextMentionTermination("TERMINATE")
max_messages_termination = MaxMessageTermination(max_messages=3)
termination = text_mention_termination | max_messages_termination

# Multi-Agent Team
team = SelectorGroupChat(
    [
        RoutingAgent,
        TechSupportAgent,
        AccountsBillingAgent,
        ConversationalSearchAgent,
        TravelConciergeAgent,
        FrontDeskAgent
    ],
    model_client=gpt_model_client,
    termination_condition=termination,
)

# Define the main asynchronous function
async def main():
    while True:
        user_query = input("You: ")  # Prompt for user input
        if user_query.lower() == "exit":  # Allow user to exit
            print("Thank you for having us. Have a great day!")
            break
        await Console(team.run_stream(task=user_query))

# Run the asynchronous function
if __name__ == "__main__":
    asyncio.run(main())