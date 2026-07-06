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



# ================= ADMIN VIEWS =================

def admin_home(request):
    return render(request, "ADMIN/admin_home.html")

def admin_view_therapists(request):
    t = TherapistProfile.objects.all()
    return render(request, "ADMIN/view_therapists.html", {"val": t})

def admin_therapist_action(request):
    id = request.GET.get("id")
    act = request.GET.get("act")  # approved / rejected / blocked
    t = TherapistProfile.objects.get(id=id)
    t.status = act
    t.save()
    return redirect("/admin_view_therapists")

def admin_view_users(request):
    u = UserProfile.objects.all()
    return render(request, "ADMIN/view_users.html", {"val": u})

def admin_user_action(request):
    id = request.GET.get("id")
    act = request.GET.get("act")  # block / unblock
    u = UserProfile.objects.get(id=id)
    l = u.loginid
    l.is_active = (act == "unblock")
    l.save()
    return redirect("/admin_view_users")

def admin_view_exercises(request):
    e = Exercise.objects.all()
    return render(request, "ADMIN/view_exercises.html", {"val": e})

def admin_add_exercise(request):
    if request.method == "POST":
        n = request.POST.get("name")
        d = request.POST.get("description")
        bp = request.POST.get("body_part")
        amin = request.POST.get("target_angle_min")
        amax = request.POST.get("target_angle_max")
        reps = request.POST.get("default_reps") or 10
        sets = request.POST.get("default_sets") or 3
        vid = request.FILES.get("demo_video")
        thumb = request.FILES.get("thumbnail")

        Exercise.objects.create(
            name=n, description=d, body_part=bp, target_angle_min=amin,
            target_angle_max=amax, default_reps=reps, default_sets=sets,
            demo_video=vid, thumbnail=thumb
        )
        messages.success(request, "Exercise added to library")
        return redirect("/admin_view_exercises")
    return render(request, "ADMIN/add_exercise.html")

def admin_edit_exercise(request):
    id = request.GET.get("id")
    ex = Exercise.objects.get(id=id)
    if request.method == "POST":
        ex.name = request.POST.get("name")
        ex.description = request.POST.get("description")
        ex.body_part = request.POST.get("body_part")
        ex.target_angle_min = request.POST.get("target_angle_min")
        ex.target_angle_max = request.POST.get("target_angle_max")
        ex.default_reps = request.POST.get("default_reps") or ex.default_reps
        ex.default_sets = request.POST.get("default_sets") or ex.default_sets
        ex.is_active = request.POST.get("is_active") == "on"
        if request.FILES.get("demo_video"):
            ex.demo_video = request.FILES.get("demo_video")
        if request.FILES.get("thumbnail"):
            ex.thumbnail = request.FILES.get("thumbnail")
        ex.save()
        messages.success(request, "Exercise updated")
        return redirect("/admin_view_exercises")
    return render(request, "ADMIN/edit_exercise.html", {"ex": ex})



def therapist_home(request):
    return render(request, "THERAPIST/therapist_home.html")

def therapist_view_unassigned_patients(request):
    # Patients who registered without picking a therapist
    p = UserProfile.objects.filter(therapist__isnull=True)
    return render(request, "THERAPIST/unassigned_patients.html", {"available_patients": p})

def therapist_add_patient(request):
    auth_check = require_login(request)
    if auth_check: return auth_check

    pid = request.GET.get("id")
    t = TherapistProfile.objects.get(loginid_id=request.session["lid"])
    p = UserProfile.objects.get(id=pid)
    p.therapist = t
    p.save()
    messages.success(request, f"{p.name} added to your caseload")
    return redirect("/therapist_view_patients")

def therapist_view_patients(request):
    auth_check = require_login(request)
    if auth_check: return auth_check

    t = TherapistProfile.objects.get(loginid_id=request.session["lid"])
    p = UserProfile.objects.filter(therapist=t)
    stats = {
        "total": p.count(),
        "active_plans": ExercisePlan.objects.filter(therapist=t, is_active=True).count(),
    }
    return render(request, "THERAPIST/view_patients.html", {"val": p, "stats": stats})


def therapist_patient_detail(request):
    id = request.GET.get("id")
    p = UserProfile.objects.get(id=id)
    plans = ExercisePlan.objects.filter(patient=p).order_by("-created_date")
    history = MedicalHistory.objects.filter(user=p).order_by("-created_date")
    return render(request, "THERAPIST/patient_detail.html", {"patient": p, "plans": plans, "history": history})

def therapist_create_plan(request):
    auth_check = require_login(request)
    if auth_check: return auth_check

    pid = request.GET.get("patient_id")
    p = UserProfile.objects.get(id=pid)
    t = TherapistProfile.objects.get(loginid_id=request.session["lid"])

    if request.method == "POST":
        title = request.POST.get("title")
        goal = request.POST.get("goal")
        sd = request.POST.get("start_date") or None
        ed = request.POST.get("end_date") or None

        plan = ExercisePlan.objects.create(patient=p, therapist=t, title=title, goal=goal, start_date=sd, end_date=ed)
        messages.success(request, "Plan created. Now add exercises to it.")
        return redirect(f"/therapist_edit_plan_items?id={plan.id}")
    return render(request, "THERAPIST/create_plan.html", {"patient": p})

def therapist_edit_plan_items(request):
    id = request.GET.get("id")
    plan = ExercisePlan.objects.get(id=id)

    if request.method == "POST":
        exid = request.POST.get("exercise_id")
        ex = Exercise.objects.get(id=exid)
        sets = request.POST.get("prescribed_sets") or 3
        reps = request.POST.get("prescribed_reps") or 10
        freq = request.POST.get("frequency_per_week") or 3
        instr = request.POST.get("instructions")

        ExercisePlanItem.objects.create(
            plan=plan, exercise=ex, prescribed_sets=sets, prescribed_reps=reps,
            frequency_per_week=freq, instructions=instr
        )
        messages.success(request, "Exercise added to plan")
        return redirect(f"/therapist_edit_plan_items?id={plan.id}")

    ex = Exercise.objects.filter(is_active=True)
    return render(request, "THERAPIST/edit_plan_items.html", {"plan": plan, "items": plan.items.all(), "exercises": ex})

def therapist_view_sessions(request):
    auth_check = require_login(request)
    if auth_check: return auth_check

    t = TherapistProfile.objects.get(loginid_id=request.session["lid"])
    s = ExerciseSession.objects.filter(plan_item__plan__therapist=t).order_by("-started_date")
    return render(request, "THERAPIST/view_sessions.html", {"val": s})

def therapist_view_session_report(request):
    id = request.GET.get("id")  # session id
    r = PerformanceReport.objects.filter(session_id=id)
    frames = PoseFrameLog.objects.filter(session_id=id).order_by("frame_number")
    return render(request, "THERAPIST/view_report.html", {"val": r, "frames": frames})

def therapist_review_report(request):
    from django.utils import timezone
    id = request.GET.get("id")  # report id
    act = request.GET.get("act")  # reviewed / flagged
    r = PerformanceReport.objects.get(id=id)
    t = TherapistProfile.objects.get(loginid_id=request.session["lid"])

    if act == "reviewed":
        r.flagged_for_review = False
        r.reviewed_by = t
        r.reviewed_date = timezone.now()
    elif act == "flagged":
        r.flagged_for_review = True

    r.save()
    return redirect("/therapist_view_sessions")

# ================= PATIENT VIEWS =================

def user_home(request):
    return render(request, "USER/user_home.html")

def user_view_plans(request):
    auth_check = require_login(request)
    if auth_check: return auth_check

    u = UserProfile.objects.get(loginid_id=request.session["lid"])
    p = ExercisePlan.objects.filter(patient=u, is_active=True)
    return render(request, "USER/view_plans.html", {"val": p})

def user_medical_history(request):
    auth_check = require_login(request)
    if auth_check: return auth_check

    u = UserProfile.objects.get(loginid_id=request.session["lid"])
    if request.method == "POST":
        cond = request.POST.get("condition")
        desc = request.POST.get("description")
        dd = request.POST.get("diagnosed_date") or None
        inj = request.POST.get("injury_type")
        notes = request.POST.get("notes")

        MedicalHistory.objects.create(
            user=u, condition=cond, description=desc, diagnosed_date=dd, injury_type=inj, notes=notes
        )
        messages.success(request, "Medical record added")
        return redirect("/user_medical_history")

    h = MedicalHistory.objects.filter(user=u).order_by("-created_date")
    return render(request, "USER/medical_history.html", {"val": h})



def user_start_session(request):
    itemid = request.GET.get("itemid")
    if request.method == "POST":
        try:
            u = UserProfile.objects.get(loginid_id=request.session["lid"])
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found. Please log in as a patient.")
            return redirect("/login")

        if not itemid:
            messages.error(request, "Invalid exercise selection")
            return redirect("/user_view_plans")

        try:
            item = ExercisePlanItem.objects.get(id=itemid)
        except ExercisePlanItem.DoesNotExist:
            messages.error(request, "Exercise not found")
            return redirect("/user_view_plans")

        s = ExerciseSession.objects.create(patient=u, plan_item=item)
        messages.success(request, "Session started")
        return redirect(f"/user_session_tracker?id={s.id}")

    item = None
    if itemid:
        try:
            item = ExercisePlanItem.objects.get(id=itemid)
        except ExercisePlanItem.DoesNotExist:
            pass
    return render(request, "USER/start_session.html", {"itemid": itemid, "item": item})

def user_session_tracker(request):
    id = request.GET.get("id")
    s = ExerciseSession.objects.get(id=id)
    return render(request, "USER/session_tracker.html", {"session": s})

def user_submit_frame(request):
    import json
    if request.method == "POST":
        payload = json.loads(request.body)
        s = ExerciseSession.objects.get(id=payload.get("session_id"), status="in_progress")
        ex = s.plan_item.exercise

        angle = float(payload.get("joint_angle"))
        if ex.target_angle_min <= angle <= ex.target_angle_max:
            accuracy = 100
        else:
            deviation = min(abs(angle - ex.target_angle_min), abs(angle - ex.target_angle_max))
            accuracy = max(0, 100 - deviation)

        if accuracy >= 85:
            feedback = "Great form, keep going!"
        elif accuracy >= 60:
            feedback = "Adjust your posture slightly for better alignment."
        else:
            feedback = "Posture off target - slow down and realign with the demo."

        rep_done = payload.get("is_rep_complete", False)

        PoseFrameLog.objects.create(
            session=s, frame_number=payload.get("frame_number"), timestamp_ms=payload.get("timestamp_ms"),
            joint_angle=angle, posture_accuracy=accuracy, is_rep_complete=rep_done,
            landmarks_json=json.dumps(payload.get("landmarks", {}))
        )

        if rep_done:
            s.completed_reps += 1
            s.save()

        from django.http import JsonResponse
        return JsonResponse({"status": "ok", "posture_accuracy": accuracy, "feedback": feedback, "reps": s.completed_reps})

    from django.http import JsonResponse
    return JsonResponse({"status": "invalid request"})

def user_complete_session(request):
    from django.utils import timezone
    from django.http import JsonResponse

    id = request.POST.get("id")
    s = ExerciseSession.objects.get(id=id)
    frames = PoseFrameLog.objects.filter(session=s)

    avg = 0
    if frames.exists():
        avg = round(sum(f.posture_accuracy for f in frames) / frames.count(), 2)

    s.status = "completed"
    s.ended_date = timezone.now()
    s.avg_accuracy = avg
    s.completed_sets = request.POST.get("completed_sets") or s.completed_sets
    s.duration_seconds = int((s.ended_date - s.started_date).total_seconds())
    s.save()

    PerformanceReport.objects.get_or_create(
        session=s,
        defaults={
            "overall_score": avg,
            "repetition_accuracy": avg,
            "posture_feedback": "Great form, keep going!" if avg >= 85 else "Adjust your posture slightly for better alignment.",
            "flagged_for_review": avg < 60,
        }
    )
    messages.success(request, "Session completed")
    return redirect("/user_view_sessions")


def user_download_report(request):
    id = request.GET.get("id")  # session id
    r = PerformanceReport.objects.get(session_id=id)
    if r.report_file:
        return redirect(r.report_file.url)
    messages.error(request, "Report not available yet")
    return redirect("/user_view_sessions")

