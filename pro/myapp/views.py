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

def admin_view_feedback(request):
    f = Feedback.objects.all().order_by("-created_date")
    return render(request, "ADMIN/view_feedback.html", {"val": f})

def admin_view_reports(request):
    c = Complaint.objects.all().order_by("-created_date")
    return render(request, "ADMIN/view_reports.html", {"val": c})

# ================= THERAPIST VIEWS =================

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

        itemid = request.POST.get("itemid")
        video = request.FILES.get("video")

        if not itemid:
            messages.error(request, "Invalid exercise selection")
            return redirect("/user_view_plans")

        if not video:
            messages.error(request, "Please upload a video of yourself performing the exercise")
            return redirect(f"/user_start_session?itemid={itemid}")

        try:
            item = ExercisePlanItem.objects.get(id=itemid)
        except ExercisePlanItem.DoesNotExist:
            messages.error(request, "Exercise not found")
            return redirect("/user_view_plans")

        s = ExerciseSession.objects.create(patient=u, plan_item=item, recorded_video=video, status="processing")

        try:
            from .cv_video_analysis import analyze_recorded_video
            analyze_recorded_video(s)
        except Exception as e:
            s.status = "aborted"
            s.save()
            messages.error(request, f"Could not analyze the video: {e}")
            return redirect("/user_view_plans")

        messages.success(request, "Video analyzed. Here's how it went.")
        return redirect(f"/user_session_result?id={s.id}")

    item = None
    if itemid:
        try:
            item = ExercisePlanItem.objects.get(id=itemid)
        except ExercisePlanItem.DoesNotExist:
            pass
    return render(request, "USER/start_session.html", {"itemid": itemid, "item": item})

def user_session_result(request):
    id = request.GET.get("id")
    s = ExerciseSession.objects.get(id=id)
    report = PerformanceReport.objects.filter(session=s).first()
    frames = PoseFrameLog.objects.filter(session=s).order_by("frame_number")
    return render(request, "USER/session_result.html", {"session": s, "report": report, "frames": frames})

def user_view_sessions(request):
    auth_check = require_login(request)
    if auth_check: return auth_check

    u = UserProfile.objects.get(loginid_id=request.session["lid"])
    sessions = ExerciseSession.objects.filter(patient=u).order_by("-started_date")

    # Annotate each session with feedback status
    for s in sessions:
        s.has_feedback = Feedback.objects.filter(user=u, session=s).exists()

    return render(request, "USER/view_sessions.html", {"val": sessions})

def user_download_report(request):
    id = request.GET.get("id")  # session id
    r = PerformanceReport.objects.get(session_id=id)
    if r.report_file:
        return redirect(r.report_file.url)
    messages.error(request, "Report not available yet")
    return redirect("/user_view_sessions")

def user_add_feedback(request):
    try:
        u = UserProfile.objects.get(loginid_id=request.session["lid"])
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found")
        return redirect("/login")

    session_id = request.GET.get("session_id")
    if not session_id:
        messages.error(request, "No session specified")
        return redirect("/user_view_sessions")

    try:
        session = ExerciseSession.objects.get(id=session_id, patient=u)
    except ExerciseSession.DoesNotExist:
        messages.error(request, "Session not found")
        return redirect("/user_view_sessions")

    if session.status != "completed":
        messages.error(request, "Feedback can only be provided after the session is completed.")
        return redirect("/user_view_sessions")

    existing = Feedback.objects.filter(user=u, session=session).first()
    if existing:
        messages.info(request, "You already submitted feedback for this session. You can edit it.")
        return redirect(f"/user_edit_feedback/?id={existing.id}")

    if request.method == "POST":
        msg = request.POST.get("message")
        rt = request.POST.get("rating")
        Feedback.objects.create(user=u, session=session, message=msg, rating=rt)
        messages.success(request, "Feedback submitted successfully!")
        return redirect("/user_view_sessions")

    return render(request, "USER/add_feedback.html", {"session": session})

def user_edit_feedback(request):
    try:
        u = UserProfile.objects.get(loginid_id=request.session["lid"])
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found")
        return redirect("/login")

    feedback_id = request.GET.get("id")
    try:
        feedback = Feedback.objects.get(id=feedback_id, user=u)
    except Feedback.DoesNotExist:
        messages.error(request, "Feedback not found")
        return redirect("/user_view_feedback")

    if request.method == "POST":
        feedback.message = request.POST.get("message")
        feedback.rating = request.POST.get("rating")
        feedback.save()
        messages.success(request, "Feedback updated successfully!")
        return redirect("/user_view_feedback")

    return render(request, "USER/edit_feedback.html", {"feedback": feedback})

def user_delete_feedback(request):
    try:
        u = UserProfile.objects.get(loginid_id=request.session["lid"])
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found")
        return redirect("/login")

    feedback_id = request.GET.get("id")
    try:
        feedback = Feedback.objects.get(id=feedback_id, user=u)
        feedback.delete()
        messages.success(request, "Feedback deleted successfully!")
    except Feedback.DoesNotExist:
        messages.error(request, "Feedback not found")

    return redirect("/user_view_feedback")

def user_view_feedback(request):
    try:
        u = UserProfile.objects.get(loginid_id=request.session["lid"])
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found")
        return redirect("/login")
    f = Feedback.objects.filter(user=u).order_by("-created_date")
    return render(request, "USER/view_feedback.html", {"val": f})

def user_add_complaint(request):
    try:
        u = UserProfile.objects.get(loginid_id=request.session["lid"])
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found")
        return redirect("/login")

    session_id = request.GET.get("session_id")
    session = None
    if session_id:
        try:
            session = ExerciseSession.objects.get(id=session_id, patient=u, status="completed")
        except ExerciseSession.DoesNotExist:
            messages.error(request, "Invalid session reference.")
            return redirect("/user_view_sessions")
    else:
        has_session = ExerciseSession.objects.filter(patient=u, status="completed").exists()
        if not has_session:
            messages.error(request, "Complaints can only be filed after completing a session.")
            return redirect("/user_home")

    if request.method == "POST":
        sub = request.POST.get("subject")
        msg = request.POST.get("message")
        Complaint.objects.create(user=u, session=session, subject=sub, message=msg)
        messages.success(request, "Report/Complaint filed")
        return redirect("/user_view_sessions")
    return render(request, "USER/add_complaint.html", {"session": session})

def user_view_complaints(request):
    auth_check = require_login(request)
    if auth_check: return auth_check

    try:
        u = UserProfile.objects.get(loginid_id=request.session["lid"])
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found")
        return redirect("/login")
    c = Complaint.objects.filter(user=u).order_by("-created_date")
    return render(request, "USER/view_reports.html", {"val": c})
