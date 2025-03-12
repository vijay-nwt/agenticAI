from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Profile, Record, Techsupport, AccountInfo

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .autogen_service import execute_crud
from decimal import Decimal

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

# @login_required
def accounts(request):
    accounts = AccountInfo.objects.all()
    return render(request, 'account.html', {'accounts': accounts})

# @login_required
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

# @login_required
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

# @login_required
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

@csrf_exempt
def account_info_detail(request, pk):
    try:
        account = get_object_or_404(AccountInfo, pk=pk)
        if request.method == 'GET':
            data = {
                'username': account.username,
                'account_balance': str(account.account_balance),
                'last_transactions': account.last_transactions,
                'contact_details': account.contact_details
            }
            return JsonResponse(data)
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    except AccountInfo.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Failed to fetch account details: {str(e)}'}, status=500)

@csrf_exempt
def create_account_info(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if not data.get('username'):
                return JsonResponse({'error': 'Username is required'}, status=400)
            
            account = AccountInfo.objects.create(
                username=data.get('username'),
                account_balance=Decimal(str(data.get('account_balance', 0.00))),
                last_transactions=data.get('last_transactions', []),
                contact_details=data.get('contact_details', '')
            )
            return JsonResponse({'id': account.id, 'message': 'Account info created successfully'}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except ValueError as e:
            return JsonResponse({'error': f'Invalid data format: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Failed to create account: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def update_account_info(request, pk):
    try:
        account = get_object_or_404(AccountInfo, pk=pk)
        if request.method == 'PUT':
            try:
                data = json.loads(request.body)
                account.username = data.get('username', account.username)
                if 'account_balance' in data:
                    account.account_balance = Decimal(str(data.get('account_balance')))
                account.last_transactions = data.get('last_transactions', account.last_transactions)
                account.contact_details = data.get('contact_details', account.contact_details)
                account.save()
                return JsonResponse({'message': 'Account info updated successfully'})
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON format'}, status=400)
            except ValueError as e:
                return JsonResponse({'error': f'Invalid data format: {str(e)}'}, status=400)
            except Exception as e:
                return JsonResponse({'error': f'Failed to update account: {str(e)}'}, status=500)
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    except AccountInfo.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)

@csrf_exempt
def handle_transaction(request, pk):
    try:
        account = get_object_or_404(AccountInfo, pk=pk)
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                if 'amount' not in data:
                    return JsonResponse({'error': 'Amount is required'}, status=400)
                
                amount = Decimal(str(data.get('amount', 0)))
                transaction_type = data.get('transaction_type')
                
                if not amount:
                    return JsonResponse({'error': 'Amount must be greater than 0'}, status=400)
                
                if transaction_type not in ['deposit', 'withdrawal']:
                    return JsonResponse({'error': 'Invalid transaction type'}, status=400)
                
                if transaction_type == 'withdrawal' and account.account_balance < amount:
                    return JsonResponse({'error': 'Insufficient funds'}, status=400)
                
                # Adjust amount based on transaction type
                if transaction_type == 'withdrawal':
                    amount = -amount
                
                # Update balance and add transaction
                account.account_balance += amount
                
                # Add to transaction history
                if not account.last_transactions:
                    account.last_transactions = []
                
                transaction_detail = f"{transaction_type.capitalize()}: {abs(amount)}"
                account.last_transactions.append(transaction_detail)
                account.last_transactions = account.last_transactions[-10:]
                
                account.save()
                
                return JsonResponse({
                    'message': 'Transaction processed successfully',
                    'new_balance': str(account.account_balance),
                    'transaction': transaction_detail
                })
                
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON format'}, status=400)
            except ValueError as e:
                return JsonResponse({'error': f'Invalid amount format: {str(e)}'}, status=400)
            except Exception as e:
                return JsonResponse({'error': f'Failed to process transaction: {str(e)}'}, status=500)
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    except AccountInfo.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)

@csrf_exempt
def delete_account_info(request, pk):
    try:
        account = get_object_or_404(AccountInfo, pk=pk)
        if request.method == 'DELETE':
            account.delete()
            return JsonResponse({'message': 'Account info deleted successfully'})
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    except AccountInfo.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Failed to delete account: {str(e)}'}, status=500)
