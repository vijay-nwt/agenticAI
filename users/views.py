from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Profile, Record, Techsupport, AccountInfo

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .autogen_service import execute_crud

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
def tech_support(request):
    tech_support = Techsupport.objects.all()
    return render(request, 'techsupport.html', {'tech_support': tech_support})

@login_required
def accounts(request):
    accounts = AccountInfo.objects.all()
    return render(request, 'techsupport.html', {'accounts': accounts})

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


@csrf_exempt
def ai_crud(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("data",data)
            prompt = data.get("prompt", "")
            response = execute_crud(prompt)  # Get the response directly
            return JsonResponse(response)  # Return the response directly
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)
