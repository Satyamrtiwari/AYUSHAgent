from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Patient, Diagnosis, AuditLog


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True) 
    class Meta:
         model = User
         fields = [ 'username' ,'email' , 'password' ]
    def create(self , validated_data):
         user = User.objects.create_user( 
              username = validated_data['username'], 
              email = validated_data['email'], 
              password = validated_data['password'] 
              )
         return user 
    

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ("user",)
    
    def validate_ayush_id(self, value):
        """Validate AYUSH ID format: AY followed by exactly 5 digits"""
        import re
        pattern = r'^AY\d{5}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "AYUSH ID must be in format: AY followed by exactly 5 digits (e.g., AY00001)"
            )
        return value


class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = '__all__'


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'