"""
URL configuration for agenticAI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from users import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name='signup'),
    path('welcome/', views.welcome, name='welcome'),
    path('', views.home, name='home'),  # Home page after login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('records/', views.record_list, name='record_list'),
    path('accounts/', views.accounts, name='accounts'),
    path('tech/', views.tech_support, name='tech_support'),
    path('records/create/', views.create_record, name='create_record'),
    path('records/<int:pk>/update/', views.update_record, name='update_record'),
    path('records/<int:pk>/delete/', views.delete_record, name='delete_record'),
    path('ai_crud/', views.ai_crud, name='ai_crud'),
    path('account_info/<int:pk>/', views.account_info_detail, name='account_info_detail'),
    path('account_info/create/', views.create_account_info, name='create_account_info'),
    path('account_info/<int:pk>/update/', views.update_account_info, name='update_account_info'),
    path('account_info/<int:pk>/transaction/', views.handle_transaction, name='handle_transaction'),
    path('account_info/<int:pk>/delete/', views.delete_account_info, name='delete_account_info')
]
