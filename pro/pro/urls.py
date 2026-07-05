"""
URL configuration for pro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.index),
    path('login/', views.login_view),
    path('signout/', views.signout),
    path('register_user/', views.register_user),
    path('register_therapist/', views.register_therapist),
 
    # ---------------- ADMIN ---------------- #
    path('admin_home/', views.admin_home),
    path('admin_view_therapists/', views.admin_view_therapists),
    path('admin_therapist_action/', views.admin_therapist_action),
    path('admin_view_users/', views.admin_view_users),
    path('admin_user_action/', views.admin_user_action),
    path('admin_view_exercises/', views.admin_view_exercises),
    path('admin_add_exercise/', views.admin_add_exercise),
    path('admin_edit_exercise/', views.admin_edit_exercise),

     path('therapist_home/', views.therapist_home),
    path('therapist_view_unassigned_patients/', views.therapist_view_unassigned_patients),
    path('therapist_add_patient/', views.therapist_add_patient),
    path('therapist_view_patients/', views.therapist_view_patients),
    # path('therapist_patient_detail/', views.therapist_patient_detail),
]
