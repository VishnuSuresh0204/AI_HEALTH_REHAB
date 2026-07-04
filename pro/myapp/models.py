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
 