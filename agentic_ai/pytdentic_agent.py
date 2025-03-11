from __future__ import annotations

import asyncio
import os
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

from pydantic_ai import Agent, RunContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Define agent types as an enum for better type safety
class AgentType(str, Enum):
    TECH_SUPPORT = "TechSupportAgent"
    ACCOUNTS_BILLING = "AccountsBillingAgent"
    CONVERSATIONAL_SEARCH = "ConversationalSearchAgent"
    TRAVEL_CONCIERGE = "TravelConciergeAgent"
    FRONT_DESK = "FrontDeskAgent"

# Dependencies container for our agents
@dataclass
class Deps:
    # Add any external API clients or resources here
    # For example, database connections, API keys, etc.
    pass

# Create the main routing agent
routing_agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt="""
    You are a planning agent. Your job is to identify the intent of the user and delegate the request to the correct agent.
    You must respond with a JSON object containing two fields:
    - "agent_type": One of "TechSupportAgent", "AccountsBillingAgent", "ConversationalSearchAgent", "TravelConciergeAgent", or "FrontDeskAgent"
    - "reasoning": A brief explanation of why you selected this agent
    
    The available agents are:
        - TechSupportAgent: For troubleshooting internet, phone, cable, or software installation.
        - AccountsBillingAgent: For account balances, plan upgrades, and payments.
        - ConversationalSearchAgent: For FAQs, product availability, and catalog filtering.
        - TravelConciergeAgent: For booking flights, hotels, and travel-related queries.
        - FrontDeskAgent: For handling appointments, service inquiries, and call transfers.
    
    Analyze the user's request and identify which agent should handle it.
    """,
    deps_type=Deps,
    retries=1,
)

# Create specialized agents
tech_support_agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt="""
    You are a tech support agent specialized in troubleshooting and resolving technical issues.
    You handle issues such as:
    - Troubleshooting internet, cable, or phone connections
    - Setting up new devices
    - Handling replacement device requests
    - Installing software
    
    Be helpful, clear, and provide step-by-step instructions when needed.
    """,
    deps_type=Deps,
    retries=1,
)

accounts_billing_agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt="""
    You are an accounts and billing agent who helps customers with their account information.
    You assist with:
    - Checking account balances and invoices
    - Upgrading or managing plans
    - Updating contact details
    - Processing payments
    
    Be precise with account information and clear about payment details.
    """,
    deps_type=Deps,
    retries=1,
)

conversational_search_agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt="""
    You are a conversational search agent who helps customers find information.
    You assist with:
    - Searching knowledge bases for support articles
    - Checking product availability
    - Answering FAQs
    - Filtering and searching catalogues
    
    Provide clear, concise answers and relevant information.
    """,
    deps_type=Deps,
    retries=1,
)

travel_concierge_agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt="""
    You are a travel concierge agent who helps customers with travel planning.
    You assist with:
    - Searching flights, hotels, and rental cars
    - Comparing costs
    - Booking, rescheduling, and canceling reservations
    - Making restaurant and sightseeing recommendations
    
    Provide personalized travel assistance and detailed recommendations.
    """,
    deps_type=Deps,
    retries=1,
)

front_desk_agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt="""
    You are a front desk agent who assists customers with general inquiries.
    You assist with:
    - Booking appointments
    - Providing information about hours and availability
    - Answering questions about services
    - Transferring calls
    
    Be welcoming, informative, and helpful.
    """,
    deps_type=Deps,
    retries=1,
)

# Main router function to delegate tasks to appropriate agents
async def route_and_respond(query: str) -> str:
    deps = Deps()
    
    # First, use the routing agent to determine which agent should handle the query
    routing_result = await routing_agent.run(query, deps=deps)
    
    # The response is a string, so we need to parse it into a dictionary
    try:
        # Try to parse the response as JSON
        agent_info = json.loads(routing_result.data)
    except (json.JSONDecodeError, TypeError):
        # If parsing fails, extract information using a fallback approach
        response_text = str(routing_result.data).strip()
        
        # Default to conversational search if we can't determine the agent
        agent_type = AgentType.CONVERSATIONAL_SEARCH
        reasoning = "Unable to determine specific agent from routing response"
        
        # Try to extract agent type from the response text
        for agent_enum in AgentType:
            if agent_enum.value in response_text:
                agent_type = agent_enum
                # Simple extraction of reasoning if possible
                parts = response_text.split(agent_enum.value, 1)
                if len(parts) > 1:
                    reasoning = parts[1].strip()
                break
        
        agent_info = {
            "agent_type": agent_type,
            "reasoning": reasoning
        }
    
    # Map agent types to actual agent instances
    agent_map = {
        AgentType.TECH_SUPPORT: tech_support_agent,
        AgentType.ACCOUNTS_BILLING: accounts_billing_agent,
        AgentType.CONVERSATIONAL_SEARCH: conversational_search_agent,
        AgentType.TRAVEL_CONCIERGE: travel_concierge_agent,
        AgentType.FRONT_DESK: front_desk_agent,
    }
    
    # Get the agent type from the routing result
    agent_type_str = agent_info.get("agent_type")
    
    # Try to convert the agent type string to an enum value
    try:
        if agent_type_str:
            agent_type = AgentType(agent_type_str)
        else:
            agent_type = AgentType.CONVERSATIONAL_SEARCH
    except ValueError:
        # If the string doesn't match any enum value, use the default
        agent_type = AgentType.CONVERSATIONAL_SEARCH
    
    # Get the appropriate agent
    selected_agent = agent_map.get(agent_type, conversational_search_agent)
    
    # Use the selected agent to handle the query
    response_result = await selected_agent.run(query, deps=deps)
    
    # Format and return the response
    formatted_response = (
        f"Query routed to: {agent_type.value}\n"
        f"Reasoning: {agent_info.get('reasoning', 'No reasoning provided')}\n\n"
        f"Response: {response_result.data}"
    )
    
    return formatted_response

# Add tools to specialized agents as needed
@tech_support_agent.tool
async def check_service_status(ctx: RunContext[Deps], service_type: str, location: str) -> Dict[str, Any]:
    """
    Check the status of a specific service in a location.
    
    Args:
        ctx: The run context
        service_type: The type of service (internet, cable, phone)
        location: The location or area to check
        
    Returns:
        Service status information
    """
    # In a real implementation, this would call an actual API
    # For demo purposes, we're returning mock data
    statuses = {
        "internet": "operational",
        "cable": "partial outage reported",
        "phone": "operational"
    }
    
    return {
        "service": service_type,
        "location": location,
        "status": statuses.get(service_type.lower(), "unknown"),
        "last_updated": "2025-03-10T12:00:00Z"
    }

@accounts_billing_agent.tool
async def check_account_balance(ctx: RunContext[Deps], account_id: str) -> Dict[str, Any]:
    """
    Check the balance of a customer account.
    
    Args:
        ctx: The run context
        account_id: The customer's account ID
        
    Returns:
        Account balance information
    """
    # Mock implementation for demonstration
    # In a real system, this would query a database or API
    return {
        "account_id": account_id,
        "current_balance": 125.50,
        "due_date": "2025-04-01",
        "last_payment": {
            "amount": 120.00,
            "date": "2025-03-01"
        }
    }

@travel_concierge_agent.tool
async def search_flights(
    ctx: RunContext[Deps], 
    origin: str, 
    destination: str, 
    departure_date: str,
    return_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for available flights.
    
    Args:
        ctx: The run context
        origin: Origin airport or city
        destination: Destination airport or city
        departure_date: Departure date (YYYY-MM-DD)
        return_date: Return date for round trips (YYYY-MM-DD)
        
    Returns:
        List of available flights
    """
    # Mock implementation
    return [
        {
            "airline": "Example Airlines",
            "flight_number": "EA123",
            "origin": origin,
            "destination": destination,
            "departure": f"{departure_date}T08:00:00Z",
            "arrival": f"{departure_date}T10:30:00Z",
            "price": 299.99,
            "seats_available": 15
        },
        {
            "airline": "Sample Airways",
            "flight_number": "SA456",
            "origin": origin,
            "destination": destination,
            "departure": f"{departure_date}T14:15:00Z",
            "arrival": f"{departure_date}T16:45:00Z",
            "price": 349.99,
            "seats_available": 8
        }
    ]

# Interactive CLI
async def interactive_cli():
    print("Welcome to the AI Agent System! Type 'exit' to quit.")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            print("Thank you for using our service. Goodbye!")
            break
        
        try:
            response = await route_and_respond(user_input)
            print(f"\nAI: {response}")
        except Exception as e:
            print(f"\nError: {str(e)}")
            import traceback
            traceback.print_exc()

# Function for synchronous use
def route_and_respond_sync(query: str) -> str:
    """Synchronous wrapper for the routing function"""
    return asyncio.run(route_and_respond(query))

# Entry point
if __name__ == "__main__":
    asyncio.run(interactive_cli())