from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['role'] = user.role
        token['company_id'] = user.company.id if user.company else None
        token['company_name'] = user.company.name if user.company else None
        token['warehouse_id'] = user.warehouse.id if user.warehouse else None
        token['warehouse_name'] = user.warehouse.name if user.warehouse else None

        return token