from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import AgentEvent, ChatMessage
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

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

    After all tasks are complete, summarize the findings and end with "TERMINATE".
    
    """
)

# # Tech Support Agent
# TechSupportAgent = AssistantAgent(
#     "TechSupportAgent",
#     model_client=gpt_model_client,
#     system_message="""
#     You are a tech support agent. Engage in an interactive troubleshooting session.
#     Ask follow-up questions and guide the user step-by-step to solve their internet issue.
#     Allow them to confirm if the issue is resolved before proceeding to the next step.
#     If the issue is fixed, confirm termination of the conversation.
#     """
# )
TechSupportAgent = AssistantAgent(
    "TechSupportAgent",
    model_client=gpt_model_client,
    system_message="You handle technical support issues such as troubleshooting, device setup, and software installation."
)

# Accounts and Billing Agent
AccountsBillingAgent = AssistantAgent(
    "AccountsBillingAgent",
    model_client=gpt_model_client,
    system_message="You manage account details, billing, plan upgrades, and payments."
)

# Conversational Search Agent
ConversationalSearchAgent = AssistantAgent(
    "ConversationalSearchAgent",
    model_client=gpt_model_client,
    system_message="You search FAQs, knowledge bases, and product availability."
)

# Travel Concierge Agent
TravelConciergeAgent = AssistantAgent(
    "TravelConciergeAgent",
    model_client=gpt_model_client,
    system_message="You assist users with travel bookings, comparisons, and recommendations."
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



    
# def main():
#     print("Welcome to Tech Support! Type 'exit' anytime to end the session.")
    
#     async def chat():
#         while True:
#             user_input = input("You: ")
#             if user_input.lower() == "exit":
#                 print("Thank you for using Tech Support. Have a great day!")
#                 break
#             response = await team.run(task=user_input)
#             print("AI:", response)

#     asyncio.run(chat())

# if __name__ == "__main__":
#     main()