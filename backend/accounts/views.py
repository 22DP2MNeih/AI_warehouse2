from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserRegistrationSerializer, UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet to manage company employees (Roles and accounts).
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
