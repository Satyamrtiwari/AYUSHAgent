from django.contrib import admin
from .models import Patient, Diagnosis , AuditLog
# Register your models here.

admin.site.register(Patient)
admin.site.register(Diagnosis)
admin.site.register(AuditLog)