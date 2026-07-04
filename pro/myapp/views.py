from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import *
from datetime import datetime
 
# Helper function to check if user is logged in
def require_login(request, redirect_url="/login"):
    if "lid" not in request.session:
        messages.error(request, "Please log in to access this page")
        return redirect(redirect_url)
    return None
 
def index(request):
    logout(request)
    return render(request, "index.html")
 
def login_view(request):
    if request.method == "POST":
        u = request.POST.get("username")
        p = request.POST.get("password")
        user = authenticate(username=u, password=p)
        if user:
            if user.userType == "admin":
                login(request, user)
                request.session["lid"] = user.id
                return redirect("/admin_home")
            elif user.userType == "patient":
                login(request, user)
                request.session["lid"] = user.id
                return redirect("/user_home")
            elif user.userType == "therapist":
                t = TherapistProfile.objects.get(loginid=user)
                if t.status == "approved":
                    login(request, user)
                    request.session["lid"] = user.id
                    return redirect("/therapist_home")
                else:
                    messages.error(request, f"Access denied. Account status: {t.status}")
                    return redirect("/login")
        else:
            messages.error(request, "Invalid username or password")
            return redirect("/login")
    return render(request, "login.html")
 
def signout(request):
    logout(request)
    return redirect("/")
 
# ================= REGISTRATION =================
 
def register_user(request):
    t = TherapistProfile.objects.filter(status="approved")
    if request.method == "POST":
        u = request.POST.get("username")
        p = request.POST.get("password")
        n = request.POST.get("name")
        e = request.POST.get("email")
        ph = request.POST.get("phone")
        ad = request.POST.get("address")
        g = request.POST.get("gender")
        dob = request.POST.get("dob") or None
        tid = request.POST.get("therapist")  # Can be empty
        pic = request.FILES.get("profile_pic")
 
        if Login.objects.filter(username=u).exists():
            messages.error(request, "Username already exists")
            return redirect("/register_user")
 
        l = Login.objects.create_user(username=u, password=p, userType="patient", viewPass=p)
 
        assigned_therapist = None
        if tid:
            assigned_therapist = TherapistProfile.objects.get(id=tid)
 
        UserProfile.objects.create(
            loginid=l, name=n, email=e, phone=ph, address=ad,
            gender=g, dob=dob, therapist=assigned_therapist, profile_pic=pic
        )
        messages.success(request, "Registration successful")
        return redirect("/login")
    return render(request, "user_register.html", {"therapists": t})
 
def register_therapist(request):
    if request.method == "POST":
        u = request.POST.get("username")
        p = request.POST.get("password")
        n = request.POST.get("name")
        e = request.POST.get("email")
        ph = request.POST.get("phone")
        sp = request.POST.get("specialization")
        lic = request.POST.get("license_number")
        yrs = request.POST.get("years_of_experience") or 0
        pic = request.FILES.get("profile_pic")
 
        if Login.objects.filter(username=u).exists():
            messages.error(request, "Username already exists")
            return redirect("/register_therapist")
 
        l = Login.objects.create_user(username=u, password=p, userType="therapist", viewPass=p)
        TherapistProfile.objects.create(
            loginid=l, name=n, email=e, phone=ph, specialization=sp,
            license_number=lic, years_of_experience=yrs, profile_pic=pic
        )
        messages.success(request, "Registration successful. Wait for admin approval.")
        return redirect("/login")
    return render(request, "therapist_register.html")
 