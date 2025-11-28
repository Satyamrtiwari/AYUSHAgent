from django.shortcuts import render
from rest_framework.generics import CreateAPIView , ListCreateAPIView ,RetrieveUpdateDestroyAPIView
from django.contrib.auth.models import User 
from .models import Patient, Diagnosis , AuditLog
from .serializers import RegisterSerializer 
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import PatientSerializer, DiagnosisSerializer
# Create your views here.

class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny] 

class PatientListCreateView(generics.ListCreateAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except Exception as e:
            # Handle IntegrityError (duplicate AYUSH ID) specifically
            from django.db import IntegrityError
            from rest_framework.exceptions import ValidationError
            
            if isinstance(e, IntegrityError):
                error_str = str(e).lower()
                # Only raise duplicate error if it's actually about unique constraint
                if 'unique constraint' in error_str or 'duplicate key' in error_str or 'already exists' in error_str:
                    raise ValidationError({
                        'ayush_id': ['This AYUSH ID already exists. Please use a different one.']
                    })
                else:
                    # Other integrity errors - show generic message
                    raise ValidationError({
                        'non_field_errors': ['Database error occurred. Please try again.']
                    })
            # Re-raise other exceptions (like ValidationError from serializer)
            raise


class PatientRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user)
    
class DiagnosisListCreateView(generics.ListCreateAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Diagnosis.objects.filter(patient__user=self.request.user)

    def perform_create(self, serializer):
        patient = serializer.validated_data.get("patient")
        if not patient:
            raise ValidationError({"patient": "This field is required."})
        if patient.user != self.request.user:
            raise PermissionDenied("You cannot add diagnoses to another user's patient.")
        serializer.save()

class DiagnosisRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DiagnosisSerializer    
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Diagnosis.objects.filter(patient__user=self.request.user)

    def perform_update(self, serializer):
        patient = serializer.validated_data.get("patient")
        if patient and patient.user != self.request.user:
            raise PermissionDenied("You cannot assign diagnoses to another user's patient.")
        serializer.save()


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Patient, Diagnosis, AuditLog

# Lazy import to avoid errors during migrations
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from .agents.langgraph_pipeline import LangGraphAYUSHPipeline
        _pipeline = LangGraphAYUSHPipeline()
    return _pipeline

class RunPipeline(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # -----------------------------
        # 1. SAFELY READ INPUT FIELDS
        # -----------------------------
        patient_id = request.data.get("patient_id")
        raw_text = request.data.get("raw_text")
        auto_push = bool(request.data.get("auto_push", False))

        # Missing fields → return error
        if not patient_id or not raw_text:
            return Response(
                {"error": "Fields 'patient_id' and 'raw_text' are required."},
                status=400
            )

        # -----------------------------
        # 2. FETCH PATIENT
        # -----------------------------
        patient = get_object_or_404(Patient, id=patient_id, user=request.user)


        # -----------------------------
        # 3. RUN AGENTIC PIPELINE
        # -----------------------------
        try:
            pipeline = get_pipeline()
            result = pipeline.run(
                raw_text,
                f"Patient/{patient.ayush_id}",
                auto_push
            )
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Pipeline execution error: {str(e)}")
            print(f"Traceback: {error_trace}")
            return Response(
                {
                    "error": f"Pipeline execution failed: {str(e)}",
                    "details": error_trace if request.user.is_staff else None
                },
                status=500
            )

        # -----------------------------
        # 4. SAFELY EXTRACT BEST RESULT
        # -----------------------------
        if not result:
            return Response(
                {"error": "Pipeline returned empty result."},
                status=500
            )
        
        best = result.get("best", {})
        icd_code = best.get("code") or "UNK"
        confidence = result.get("confidence", 0.0)
        ayush_term = result.get("ayush_term", "Unknown")

        # -----------------------------
        # 5. STORE DIAGNOSIS IN DB
        # -----------------------------
        try:
            diag = Diagnosis.objects.create(
                patient=patient,
                ayush_term=ayush_term,
                icd_code=icd_code,
                confidence_score=confidence,
                raw_text=raw_text
            )
        except Exception as e:
            import traceback
            print(f"Diagnosis creation error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return Response(
                {
                    "error": f"Failed to save diagnosis: {str(e)}",
                    "result": result  # Return result even if save fails
                },
                status=500
            )

        # -----------------------------
        # 6. AUDIT LOG (Optional but recommended)
        # -----------------------------
        try:
            AuditLog.objects.create(
                action="run_pipeline",
                details={
                    "patient_id": patient_id,
                    "diagnosis_id": diag.id,
                    "pipeline_state": result
                }
            )
        except Exception as e:
            # Don't fail if audit log fails
            print(f"Audit log error (non-critical): {str(e)}")

        # -----------------------------
        # 7. RETURN RESPONSE
        # -----------------------------
        return Response({
            "message": "Pipeline executed successfully.",
            "diagnosis_id": diag.id,
            "result": result
        })

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get("id_token")
        if not id_token:
            return Response({"error": "Missing id_token"}, status=status.HTTP_400_BAD_REQUEST)

        client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)
        if not client_id:
            return Response(
                {"error": "Google client ID missing on server"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests

            token_info = google_id_token.verify_oauth2_token(
                id_token,
                google_requests.Request(),
                audience=client_id,
            )
        except Exception as exc:
            return Response(
                {"error": f"Invalid Google token: {str(exc)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = token_info.get("email")
        if not email:
            return Response(
                {"error": "Google token missing email claim"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = self._resolve_username(token_info)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": username},
        )
        if created:
            user.first_name = token_info.get("given_name", "")
            user.last_name = token_info.get("family_name", "")
            user.set_unusable_password()
            user.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
            }
        )

    def _resolve_username(self, token_info):
        base = token_info.get("given_name") or token_info.get("email", "googleuser").split("@")[0]
        base = base.replace(" ", "").lower()[:20] or "user"
        candidate = base
        counter = 1
        while User.objects.filter(username=candidate).exists():
            candidate = f"{base}{counter}"
            counter += 1
        return candidate[:150]
