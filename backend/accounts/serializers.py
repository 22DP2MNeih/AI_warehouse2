from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

import re
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'role')

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r"[a-zA-Z]", value):
            raise serializers.ValidationError("Password must contain at least one letter.")
        if not re.search(r"\d", value):
            raise serializers.ValidationError("Password must contain at least one number.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise serializers.ValidationError("Password must contain at least one symbol.")
        return value

    def validate_email(self, value):
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", value):
             raise serializers.ValidationError("Please enter a valid, logical email address.")
        
        # Pārbauda vai e-pasts existē
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        return value

    def create(self, validated_data):
        
        user = User.objects.create_user(
            username=validated_data.get('email'),
            email=validated_data.get('email'),
            password=validated_data['password'],
            role=validated_data.get('role', 'MECHANIC'),
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'role')
