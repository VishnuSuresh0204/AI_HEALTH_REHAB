from django.db import models
from django.contrib.auth.models import AbstractUser
 
 
# ---------------- LOGIN ---------------- #
 
class Login(AbstractUser):
    userType = models.CharField(
        max_length=50
    )
 
    viewPass = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
 
    def __str__(self):
        return self.username
 
 
# ---------------- PATIENT PROFILE ---------------- #
 
class UserProfile(models.Model):
    loginid = models.ForeignKey(
        Login,
        on_delete=models.CASCADE
    )
 
    name = models.CharField(max_length=200)
 
    email = models.EmailField()
 
    phone = models.CharField(max_length=20)
 
    gender = models.CharField(
        max_length=10,
        null=True,
        blank=True
    )
 
    dob = models.DateField(
        null=True,
        blank=True
    )
 
    address = models.TextField(
        null=True,
        blank=True
    )
 
    emergency_contact = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
 
    height_cm = models.FloatField(
        null=True,
        blank=True
    )
 
    weight_kg = models.FloatField(
        null=True,
        blank=True
    )
 
    profile_pic = models.ImageField(
        upload_to="user_profiles",
        null=True,
        blank=True
    )
 
    therapist = models.ForeignKey(
        "TherapistProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patients"
    )
 
    def __str__(self):
        return self.name
 
 
# ---------------- THERAPIST PROFILE ---------------- #
 
class TherapistProfile(models.Model):
    loginid = models.ForeignKey(
        Login,
        on_delete=models.CASCADE
    )
 
    name = models.CharField(max_length=200)
 
    email = models.EmailField()
 
    phone = models.CharField(max_length=20)
 
    specialization = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )
 
    license_number = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
 
    years_of_experience = models.IntegerField(
        default=0
    )
 
    profile_pic = models.ImageField(
        upload_to="therapist_profiles",
        null=True,
        blank=True
    )
 
    status = models.CharField(
        max_length=20,
        default="pending"  # pending / approved / rejected / blocked
    )
 
    def __str__(self):
        return self.name


# ---------------- MEDICAL HISTORY ---------------- #
 
class MedicalHistory(models.Model):
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="medical_history"
    )
 
    condition = models.CharField(
        max_length=255
    )
 
    description = models.TextField(
        null=True,
        blank=True
    )
 
    diagnosed_date = models.DateField(
        null=True,
        blank=True
    )
 
    injury_type = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
 
    notes = models.TextField(
        null=True,
        blank=True
    )
 
    created_date = models.DateTimeField(
        auto_now_add=True
    )
 
    def __str__(self):
        return f"{self.condition} - {self.user.name}"
 

 
# ---------------- EXERCISE (LIBRARY) ---------------- #
 
class Exercise(models.Model):
 
    BODY_PART_CHOICES = (
        ("shoulder", "Shoulder"),
        ("knee", "Knee"),
        ("elbow", "Elbow"),
        ("hip", "Hip"),
        ("spine", "Spine"),
        ("ankle", "Ankle"),
        ("full_body", "Full Body"),
    )
 
    name = models.CharField(
        max_length=150
    )
 
    description = models.TextField(
        null=True,
        blank=True
    )
 
    body_part = models.CharField(
        max_length=20,
        choices=BODY_PART_CHOICES
    )
 
    target_angle_min = models.FloatField()
 
    target_angle_max = models.FloatField()
 
    default_reps = models.IntegerField(
        default=10
    )
 
    default_sets = models.IntegerField(
        default=3
    )
 
    demo_video = models.FileField(
        upload_to="exercise_demos/",
        null=True,
        blank=True
    )
 
    thumbnail = models.ImageField(
        upload_to="exercise_thumbnails/",
        null=True,
        blank=True
    )
 
    is_active = models.BooleanField(
        default=True
    )
 
    created_date = models.DateTimeField(
        auto_now_add=True
    )
 
    def __str__(self):
        return self.name
 
 
# ---------------- EXERCISE PLAN ---------------- #
 
class ExercisePlan(models.Model):
    patient = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="exercise_plans"
    )
 
    therapist = models.ForeignKey(
        TherapistProfile,
        on_delete=models.CASCADE,
        related_name="created_plans"
    )
 
    title = models.CharField(
        max_length=200
    )
 
    goal = models.TextField(
        null=True,
        blank=True
    )
 
    start_date = models.DateField(
        null=True,
        blank=True
    )
 
    end_date = models.DateField(
        null=True,
        blank=True
    )
 
    is_active = models.BooleanField(
        default=True
    )
 
    created_date = models.DateTimeField(
        auto_now_add=True
    )
 
    def __str__(self):
        return f"{self.title} - {self.patient.name}"
 


 
# ---------------- EXERCISE PLAN ITEM ---------------- #
 
class ExercisePlanItem(models.Model):
    plan = models.ForeignKey(
        ExercisePlan,
        on_delete=models.CASCADE,
        related_name="items"
    )
 
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.PROTECT,
        related_name="plan_items"
    )
 
    prescribed_sets = models.IntegerField(
        default=3
    )
 
    prescribed_reps = models.IntegerField(
        default=10
    )
 
    frequency_per_week = models.IntegerField(
        default=3
    )
 
    instructions = models.TextField(
        null=True,
        blank=True
    )
 
    def __str__(self):
        return f"{self.exercise.name} - {self.plan.title}"
 
 
# ---------------- EXERCISE SESSION ---------------- #
 
class ExerciseSession(models.Model):
 
    STATUS_CHOICES = (
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("aborted", "Aborted"),
    )
 
    patient = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="sessions"
    )
 
    plan_item = models.ForeignKey(
        ExercisePlanItem,
        on_delete=models.CASCADE,
        related_name="sessions"
    )
 
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="in_progress"
    )
 
    recorded_video = models.FileField(
        upload_to="session_recordings/",
        null=True,
        blank=True
    )
 
    completed_reps = models.IntegerField(
        default=0
    )
 
    completed_sets = models.IntegerField(
        default=0
    )
 
    avg_accuracy = models.FloatField(
        null=True,
        blank=True
    )
 
    duration_seconds = models.IntegerField(
        null=True,
        blank=True
    )
 
    started_date = models.DateTimeField(
        auto_now_add=True
    )
 
    ended_date = models.DateTimeField(
        null=True,
        blank=True
    )
 
    def __str__(self):
        return f"{self.patient.name} - {self.plan_item.exercise.name}"
 