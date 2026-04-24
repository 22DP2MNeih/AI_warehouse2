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

    def get_queryset(self):
        user = self.request.user
        if not user.company:
            return User.objects.none()
        # CEOs can see all users in their company
        return User.objects.filter(company=user.company).exclude(id=user.id)

    def destroy(self, request, *args, **kwargs):
        # Prevent self-deletion if they somehow bypass the filter
        user_to_delete = self.get_object()
        if user_to_delete == request.user:
            return Response({"error": "You cannot delete your own account."}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)