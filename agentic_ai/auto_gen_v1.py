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
import aiohttp
from tavily import TavilyClient

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# OpenAI Client
gpt_model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key=API_KEY
)

# Update base URL to match your Django API structure
BASE_API_URL = "http://localhost:8000/account_info/"

# Define external tools/functions that agents can use

async def create_account_info(username: str, account_balance: float, last_transactions: list, contact_details: str) -> str:
    """Create new account information"""
    url = f"{BASE_API_URL}create/"
    payload = {
        "username": username,
        "account_balance": account_balance,
        "last_transactions": last_transactions,
        "contact_details": contact_details
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 201:
                data = await response.json()
                return f"Account created successfully. ID: {data['id']}"
            return f"Error creating account: {await response.text()}"

async def get_account_info(account_id: str) -> str:
    """Get account information by ID"""
    url = f"{BASE_API_URL}{account_id}/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return f"Account Info:Account Holder: {data['username']}, Balance: {data['account_balance']}, Transactions: {data['last_transactions']}, Contact: {data['contact_details']}"
            return f"Error fetching account info: {await response.text()}"

async def update_account_info(username: str, account_id: str, account_balance: float, last_transactions: list, contact_details: str) -> str:
    """Update existing account information"""
    url = f"{BASE_API_URL}{account_id}/update/"
    payload = {
        "username": username,
        "account_balance": account_balance,
        "last_transactions": last_transactions,
        "contact_details": contact_details
    }
    async with aiohttp.ClientSession() as session:
        async with session.put(url, json=payload) as response:
            if response.status == 200:
                return "Account updated successfully"
            return f"Error updating account: {await response.text()}"

async def delete_account_info(account_id: str) -> str:
    """Delete account information"""
    url = f"{BASE_API_URL}{account_id}/delete/"
    async with aiohttp.ClientSession() as session:
        async with session.delete(url) as response:
            if response.status == 200:
                return "Account deleted successfully"
            return f"Error deleting account: {await response.text()}"

async def handle_transaction(account_id: str, amount: float, transaction_type: str) -> str:
    """Handle deposit/withdrawal transaction and update balance"""
    url = f"{BASE_API_URL}{account_id}/transaction/"
    payload = {
        "amount": amount,
        "transaction_type": transaction_type  # "deposit" or "withdrawal"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return f"Transaction successful. New balance: {data['new_balance']}"
            return f"Error processing transaction: {await response.text()}"

async def get_weather_info(city: str) -> str:
    """Get current weather information for a given city."""
    WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    
    if not WEATHER_API_KEY:
        return "Error: OpenWeather API key not found. Please check your .env file."
    
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    async with aiohttp.ClientSession() as session:
        try:
            params = {
                'q': city,
                'appid': WEATHER_API_KEY,
                'units': 'metric'  # For Celsius
            }
            async with session.get(base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    weather_desc = data['weather'][0]['description']
                    temp = data['main']['temp']
                    humidity = data['main']['humidity']
                    return f"Current weather in {city}: {weather_desc}, Temperature: {temp}°C, Humidity: {humidity}%"
                else:
                    return f"Error getting weather data for {city}. Status: {response.status}"
        except Exception as e:
            return f"Error making API request: {str(e)}"

async def web_search(query: str) -> str:
    """Perform a web search using Tavily API."""
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        response = tavily_client.search(query)
        return str(response)
    except Exception as e:
        return f"Error performing web search: {str(e)}"

async def get_train_between_stations(from_station: str, to_station: str) -> str:
    """Get train information between two stations using RapidAPI"""
    
    url = "https://irctc1.p.rapidapi.com/api/v3/trainBetweenStations"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "irctc1.p.rapidapi.com"
    }
    params = {
        "fromStationCode": from_station,
        "toStationCode": to_station
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return str(data)
                return f"Error fetching train data: {await response.text()}"
    except Exception as e:
        return f"Error making API request: {str(e)}"

# Create function tools
create_account_info_tool = FunctionTool(create_account_info, description="Create new account information")
get_account_info_tool = FunctionTool(get_account_info, description="Get account information by ID")
update_account_info_tool = FunctionTool(update_account_info, description="Update existing account information")
delete_account_info_tool = FunctionTool(delete_account_info, description="Delete account information")
weather_tool = FunctionTool(get_weather_info, description="Get current weather information for a given city")
handle_transaction_tool = FunctionTool(handle_transaction, description="Handle deposit/withdrawal transaction and update balance")
web_search_tool = FunctionTool(web_search, description="Perform a web search for latest or specific topic")
train_search_tool = FunctionTool(get_train_between_stations, description="Get train information between two stations")


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
        - AccountsBillingAgent: For account balances,manage account details, Contact details, and transactions.
        - ConversationalSearchAgent: For general queries ,weather information and can perform web searches to answer questions about current events or specific topics.
        - TravelConciergeAgent: For booking flights, hotels, and travel-related queries.
        - FrontDeskAgent: For handling appointments, service inquiries, call transfers, .
     You can engage with agnets multiple times

    When assigning tasks, use this format:
    1. <agent> : <task>
    After all tasks are complete, summarize the findings and end with "TERMINATE".
    
    """
)

# Tech Support Agent with tools
TechSupportAgent = AssistantAgent(
    "TechSupportAgent",
    model_client=gpt_model_client,
    system_message="""
    You handle technical support issues such as internet troubleshooting, device setup, and software installation.
    """
)

# Accounts and Billing Agent with tools
AccountsBillingAgent = AssistantAgent(
    "AccountsBillingAgent",
    model_client=gpt_model_client,
    system_message="""
    You manage account details, balance, Contact details, and transactions.
    You can handle deposits and withdrawals which will automatically update both the balance and transaction history.
    Use the handle_transaction tool with transaction_type="deposit" for deposits and transaction_type="withdrawal" for withdrawals.
    """,
    tools=[create_account_info_tool, get_account_info_tool, update_account_info_tool, 
           delete_account_info_tool, handle_transaction_tool]
)

ConversationalSearchAgent = AssistantAgent(
    "ConversationalSearchAgent",
    model_client=gpt_model_client,
    system_message="""
    You search FAQs, knowledge bases.
    You provide weather information for cities worldwide.
    You have access to real-time weather data through the OpenWeather API.
    Use the weather tool to provide accurate current weather conditions.
    use web_search_tool for perform web searches to answer questions about current events or specific topics after getting the answer from that tool , always give final response in 1-2 lines.
    """,
    tools=[weather_tool,web_search_tool]
)
# Travel Concierge Agent with tools
TravelConciergeAgent = AssistantAgent(
    "TravelConciergeAgent",
    model_client=gpt_model_client,
    system_message="""
    You assist users with travel bookings, comparisons, and recommendations.
    You can search for trains between stations using the train search tool.
    When using the train search tool, always ask for both source and destination station codes.
    """,
    tools=[train_search_tool]
)

# Front Desk Agent
FrontDeskAgent = AssistantAgent(
    "FrontDeskAgent",
    model_client=gpt_model_client,
    system_message="You handle appointment bookings, business hours, general inquiries, ",
   
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