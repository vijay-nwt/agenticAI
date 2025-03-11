from autogen_agentchat.agents import AssistantAgent, ToolAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import AgentEvent, ChatMessage
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
import asyncio
from dotenv import load_dotenv
import os
import json
import requests
from typing import Dict, List, Optional, Any

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

# Example external functions/tools that agents can call
# These would connect to your actual APIs in production

async def search_flights(departure: str, destination: str, date: str) -> Dict:
    """
    Search for available flights based on departure, destination, and date.
    
    Args:
        departure: Departure airport code
        destination: Destination airport code
        date: Date of travel in YYYY-MM-DD format
    
    Returns:
        Dictionary with flight search results
    """
    # In production, replace with actual API call
    print(f"Searching flights from {departure} to {destination} on {date}")
    
    # Simulated API response
    mock_response = {
        "flights": [
            {
                "flight_number": "BA1234",
                "airline": "British Airways",
                "departure": departure,
                "destination": destination,
                "departure_time": f"{date}T08:30:00",
                "arrival_time": f"{date}T11:45:00",
                "price": 299.99,
                "available_seats": 42
            },
            {
                "flight_number": "AA5678",
                "airline": "American Airlines",
                "departure": departure,
                "destination": destination,
                "departure_time": f"{date}T14:15:00",
                "arrival_time": f"{date}T17:30:00",
                "price": 329.99,
                "available_seats": 18
            }
        ]
    }
    return mock_response

async def get_account_details(account_id: str) -> Dict:
    """
    Retrieve account details from the billing system.
    
    Args:
        account_id: The customer's account ID
    
    Returns:
        Dictionary with account information
    """
    # In production, replace with actual database or API call
    print(f"Fetching account details for {account_id}")
    
    # Simulated database response
    mock_response = {
        "account_id": account_id,
        "customer_name": "Jane Doe",
        "email": "jane.doe@example.com",
        "plan": "Premium Plus",
        "monthly_cost": 59.99,
        "billing_cycle": "Monthly",
        "next_payment_date": "2025-04-01",
        "payment_method": "Credit Card (ending in 4321)",
        "account_status": "Active"
    }
    return mock_response

async def check_appointment_availability(service_type: str, date: str) -> Dict:
    """
    Check available appointment slots for a specific service.
    
    Args:
        service_type: Type of service requested
        date: Date in YYYY-MM-DD format
    
    Returns:
        Dictionary with available appointment slots
    """
    # In production, replace with actual calendar API call
    print(f"Checking appointment availability for {service_type} on {date}")
    
    # Simulated appointment system response
    mock_response = {
        "service": service_type,
        "date": date,
        "available_slots": [
            {"time": "09:00", "duration": "30min"},
            {"time": "10:30", "duration": "30min"},
            {"time": "14:15", "duration": "30min"},
            {"time": "16:45", "duration": "30min"}
        ]
    }
    return mock_response

async def check_internet_service_status(postal_code: str) -> Dict:
    """
    Check internet service status for a specific area.
    
    Args:
        postal_code: Customer's postal/zip code
    
    Returns:
        Dictionary with service status information
    """
    # In production, replace with actual service monitoring API
    print(f"Checking internet service status for area {postal_code}")
    
    # Simulated service status
    mock_response = {
        "postal_code": postal_code,
        "internet_status": "Operational",
        "reported_issues": 0,
        "last_outage": "2025-02-18T14:30:00",
        "expected_speeds": "Up to 500 Mbps",
        "maintenance_planned": False
    }
    return mock_response

async def create_booking(customer_name: str, service_type: str, date: str, time: str) -> Dict:
    """
    Create a new booking in the appointment system.
    
    Args:
        customer_name: Name of the customer
        service_type: Type of service requested
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format
    
    Returns:
        Dictionary with booking confirmation
    """
    # In production, replace with actual booking API
    print(f"Creating booking for {customer_name} for {service_type} on {date} at {time}")
    
    # Simulated booking confirmation
    booking_id = "BK" + "".join([str(i) for i in range(8)])
    mock_response = {
        "booking_id": booking_id,
        "status": "confirmed",
        "customer_name": customer_name,
        "service": service_type,
        "date": date,
        "time": time,
        "cancellation_policy": "Free cancellation up to 24 hours before appointment"
    }
    return mock_response

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
    You are a planning agent. Your job is to identify the intent of the user and delegate the request to the correct agent.
     You only plan and delegate tasks - you do not execute them yourself. 
     The available agents are:
        - TechSupportAgent: For troubleshooting internet, phone, cable, or software installation.
        - AccountsBillingAgent: For account balances, plan upgrades, and payments.
        - ConversationalSearchAgent: For FAQs, product availability, and catalog filtering.
        - TravelConciergeAgent: For booking flights, hotels, and travel-related queries.
        - FrontDeskAgent: For handling appointments, service inquiries, and call transfers.
     You can engage with agents multiple times.

    When assigning tasks, use this format:
    1. <agent> : <task>

    After all tasks are complete, summarize the findings and end with "TERMINATE".
    """
)

# Tool Agent for external API calls
tools = {
    "search_flights": search_flights,
    "get_account_details": get_account_details,
    "check_appointment_availability": check_appointment_availability,
    "check_internet_service_status": check_internet_service_status,
    "create_booking": create_booking
}

# Creating a ToolAgent that can execute the tools
APIToolAgent = ToolAgent(
    "APIToolAgent",
    tools=tools
)

# Tech Support Agent - with access to tools
TechSupportAgent = AssistantAgent(
    "TechSupportAgent",
    model_client=gpt_model_client,
    system_message="""
    You handle technical support issues such as troubleshooting, device setup, and software installation.
    
    You have access to external tools for checking service status and troubleshooting:
    - To check internet service status in an area, ask the APIToolAgent to use check_internet_service_status with the postal_code
    
    Always use the tools available to you through the APIToolAgent when you need real-time data.
    Format your tool requests as: @APIToolAgent Please use [tool_name] with parameters: {param1: value1, param2: value2}
    """
)

# Accounts and Billing Agent - with access to tools
AccountsBillingAgent = AssistantAgent(
    "AccountsBillingAgent",
    model_client=gpt_model_client,
    system_message="""
    You manage account details, billing, plan upgrades, and payments.
    
    You have access to external tools for retrieving account information:
    - To retrieve customer account details, ask the APIToolAgent to use get_account_details with the account_id
    
    Always use the tools available to you through the APIToolAgent when you need real-time data.
    Format your tool requests as: @APIToolAgent Please use [tool_name] with parameters: {param1: value1, param2: value2}
    """
)

# Conversational Search Agent
ConversationalSearchAgent = AssistantAgent(
    "ConversationalSearchAgent",
    model_client=gpt_model_client,
    system_message="You search FAQs, knowledge bases, and product availability."
)

# Travel Concierge Agent - with access to tools
TravelConciergeAgent = AssistantAgent(
    "TravelConciergeAgent",
    model_client=gpt_model_client,
    system_message="""
    You assist users with travel bookings, comparisons, and recommendations.
    
    You have access to external tools for travel services:
    - To search for flights, ask the APIToolAgent to use search_flights with departure, destination, and date parameters
    
    Always use the tools available to you through the APIToolAgent when you need real-time data.
    Format your tool requests as: @APIToolAgent Please use [tool_name] with parameters: {param1: value1, param2: value2}
    """
)

# Front Desk Agent - with access to tools
FrontDeskAgent = AssistantAgent(
    "FrontDeskAgent",
    model_client=gpt_model_client,
    system_message="""
    You handle appointment bookings, business hours, and general inquiries.
    
    You have access to external tools for appointments:
    - To check appointment availability, ask the APIToolAgent to use check_appointment_availability with service_type and date
    - To create a booking, ask the APIToolAgent to use create_booking with customer_name, service_type, date, and time
    
    Always use the tools available to you through the APIToolAgent when you need real-time data.
    Format your tool requests as: @APIToolAgent Please use [tool_name] with parameters: {param1: value1, param2: value2}
    """
)

# Termination Conditions
text_mention_termination = TextMentionTermination("TERMINATE")
max_messages_termination = MaxMessageTermination(max_messages=30)  # Increased to allow for tool interactions
termination = text_mention_termination | max_messages_termination

# Multi-Agent Team with ToolAgent included
team = SelectorGroupChat(
    [
        RoutingAgent,
        TechSupportAgent,
        AccountsBillingAgent,
        ConversationalSearchAgent,
        TravelConciergeAgent,
        FrontDeskAgent,
        APIToolAgent  # Include the ToolAgent in the team
    ],
    model_client=gpt_model_client,
    termination_condition=termination,
)

# Define the main asynchronous function
async def main():
    print("Welcome to our Customer Support! Type 'exit' anytime to end the session.")
    while True:
        user_query = input("You: ")  # Prompt for user input
        if user_query.lower() == "exit":  # Allow user to exit
            print("Thank you for having us. Have a great day!")
            break
        await Console(team.run_stream(task=user_query))

# Run the asynchronous function
if __name__ == "__main__":
    asyncio.run(main())