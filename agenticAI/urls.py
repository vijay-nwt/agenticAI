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
from users.views import signup, welcome, home, login_view, logout_view, record_list, create_record, update_record, delete_record

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', signup, name='signup'),
    path('welcome/', welcome, name='welcome'),
    path('', home, name='home'),  # Home page after login
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('records/', record_list, name='record_list'),
    path('records/create/', create_record, name='create_record'),
    path('records/<int:pk>/update/', update_record, name='update_record'),
    path('records/<int:pk>/delete/', delete_record, name='delete_record'),
]
