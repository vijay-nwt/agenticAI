from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Profile, Record
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from crewai import Agent, Task, Crew
from datetime import datetime
from litellm import completion
import os
from django.conf import settings

# Add this configuration at the top of your views.py
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

# Create your views here.

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)  # Create a profile for the new user
            login(request, user)
            return redirect('welcome')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def welcome(request):
    return render(request, 'welcome.html')

# @login_required
def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('welcome')  # Redirect to home after successful login
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('login')

@login_required
def record_list(request):
    records = Record.objects.all()
    return render(request, 'records.html', {'records': records})

@login_required
def create_record(request):
    if request.method == 'POST':
        # Create record from POST data
        Record.objects.create(
            name=request.POST['name'],
            age=request.POST['age'],
            address=request.POST['address'],
            department=request.POST['department']
        )
        return redirect('record_list')
    return render(request, 'record_form.html')

@login_required
def update_record(request, pk):
    record = get_object_or_404(Record, pk=pk)
    if request.method == 'POST':
        # Update record from POST data
        record.name = request.POST['name']
        record.age = request.POST['age']
        record.address = request.POST['address']
        record.department = request.POST['department']
        record.save()
        return redirect('record_list')
    return render(request, 'record_form.html', {'record': record})

@login_required
def delete_record(request, pk):
    record = get_object_or_404(Record, pk=pk)
    if request.method == 'POST':
        record.delete()
    return redirect('record_list')

def create_crew_ai_agent():
    # Define the agent
    record_manager = Agent(
        role='Record Manager',
        goal='Help users manage records by creating, updating, and deleting them',
        backstory="""You are an AI assistant specialized in record management. 
        You help users create, update, and delete records in a database.""",
        verbose=True,
        allow_delegation=False,
        llm_config={
            "config_list": [{
                "model": "gpt-4o",
                "api_key": settings.OPENAI_API_KEY
            }]
        }
    )
    return record_manager

def process_message_with_crewai(message):
    agent = create_crew_ai_agent()
    
    # Get the actual table name from the Record model
    table_name = Record._meta.db_table
    
    # Create a task for the agent with specific model context
    task = Task(
        description=f"""Process the following user request: {message}
        The user wants to manage records in a Django application. The model is defined in models.py as:
        class Record(models.Model):
            name = models.CharField(max_length=100)
            age = models.IntegerField()
            address = models.TextField()
            department = models.CharField(max_length=100)
            created_at = models.DateTimeField(auto_now_add=True)
            updated_at = models.DateTimeField(auto_now=True)
        
        The actual table name in the database is '{table_name}'.
        
        For record operations, you need to:
        1. Understand if they want to create, update, or delete a record
        2. Extract the necessary details
        3. Return a simple, direct response that can be easily parsed
        When referring to the model, always use 'Record' as the class name.
        For delete operations, just return the record ID to be deleted.
        """,
        agent=agent,
        expected_output="A simple, direct response that can be easily parsed by the API"
    )
    
    # Create the crew and execute the task
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True
    )
    
    result = crew.kickoff()
    return result

@csrf_exempt
@login_required
def chatbot_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').lower()
            
            # Process the message with CrewAI
            crewai_response = process_message_with_crewai(message)
            
            # Handle delete command
            if 'delete' in message.lower():
                try:
                    # Extract ID from the original message
                    record_id = int(''.join(filter(str.isdigit, message)))
                    record = get_object_or_404(Record, pk=record_id)
                    record.delete()
                    return JsonResponse({'response': f'Record {record_id} successfully deleted'})
                except (ValueError, IndexError):
                    return JsonResponse({'response': 'Please provide a valid record ID to delete'})
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=400)
            
            # Handle create command
            if 'create' in message.lower():
                try:
                    # Extract details from the message
                    name = message.split('name')[1].split('age')[0].strip()
                    age = int(message.split('age')[1].split('address')[0].strip())
                    address = message.split('address')[1].split('department')[0].strip()
                    department = message.split('department')[1].strip()
                    
                    # Create the record
                    Record.objects.create(
                        name=name,
                        age=age,
                        address=address,
                        department=department
                    )
                    return JsonResponse({'response': 'Record created successfully'})
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=400)
            
            # For other operations, return the string representation of the response
            return JsonResponse({'response': str(crewai_response)})
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)
