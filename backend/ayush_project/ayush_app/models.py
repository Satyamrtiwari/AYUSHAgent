from django.db import models
from django.contrib.auth.models import User

class Patient(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Many patients per user
    name = models.CharField(max_length=255)
    ayush_id = models.CharField(max_length=50, unique=True)
    age = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} ({self.ayush_id})"



class Diagnosis(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    ayush_term = models.CharField(max_length=255)
    icd_code = models.CharField(max_length=20)
    confidence_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    raw_text = models.TextField()

    def __str__(self):
        return f"{self.ayush_term} [{self.icd_code}] for {self.patient}"

class AuditLog(models.Model):
    action = models.CharField(max_length=100)
    details = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} at {self.timestamp}"
