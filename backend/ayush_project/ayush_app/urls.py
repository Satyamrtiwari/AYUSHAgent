from django.contrib import admin
from django.urls import path ,include   
from .views import MeView, RegisterView, RunPipeline, GoogleAuthView 
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import PatientListCreateView, PatientRetrieveUpdateDestroyView
from .views import DiagnosisListCreateView, DiagnosisRetrieveUpdateDestroyView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/google/', GoogleAuthView.as_view(), name='google-auth'),
    path('patients/', PatientListCreateView.as_view(), name='patient-list-create'),
    path('patients/<int:pk>/', PatientRetrieveUpdateDestroyView.as_view(), name='patient-detail'),
    path('diagnoses/', DiagnosisListCreateView.as_view(), name='diagnosis-list-create'),
    path('diagnoses/<int:pk>/', DiagnosisRetrieveUpdateDestroyView.as_view(), name='diagnosis-detail'),
    path("run_pipeline/", RunPipeline.as_view()),
    path("me/", MeView.as_view(), name="me"),


]