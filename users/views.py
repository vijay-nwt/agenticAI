from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Profile

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
