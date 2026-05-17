from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

import re
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    company_name = serializers.CharField(write_only=True, required=False)
    warehouse_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role', 'company_name', 'warehouse_name')

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
        return value

    def create(self, validated_data):
        from inventory.models import Company, Warehouse
        
        role = validated_data.get('role', 'MECHANIC')
        company_name = validated_data.pop('company_name', '').strip()
        warehouse_name = validated_data.pop('warehouse_name', '').strip()
        
        if not company_name:
            raise serializers.ValidationError({"company_name": "Uzņēmuma nosaukums ir obligāts."})
            
        if role == 'CEO':
            # Create company and warehouse if they don't exist
            company, _ = Company.objects.get_or_create(name=company_name)
            
            if not warehouse_name:
                warehouse_name = "Galvenā Noliktava"
            warehouse, _ = Warehouse.objects.get_or_create(
                company=company, 
                name=warehouse_name
            )
            
            user = User.objects.create_user(
                username=validated_data['email'],
                email=validated_data['email'],
                password=validated_data['password'],
                role=role,
                company=company,
                warehouse=warehouse,
                approved=True  # CEO is automatically approved
            )
        else:
            # For employees, lookup the company. If it doesn't exist, block registration!
            try:
                company = Company.objects.get(name=company_name)
            except Company.DoesNotExist:
                raise serializers.ValidationError({
                    "company_name": f"Uzņēmums '{company_name}' neeksistē. Tikai CEO var reģistrēt jaunu uzņēmumu."
                })
            
            user = User.objects.create_user(
                username=validated_data['email'],
                email=validated_data['email'],
                password=validated_data['password'],
                role=role,
                company=company,
                warehouse=None,  # Will be assigned by CEO during approval
                approved=False   # Pending approval
            )
            
        return user

class UserSerializer(serializers.ModelSerializer):
    company_name = serializers.StringRelatedField(source='company', read_only=True)
    warehouse_name = serializers.StringRelatedField(source='warehouse', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'company', 'warehouse', 'company_name', 'warehouse_name', 'approved')
