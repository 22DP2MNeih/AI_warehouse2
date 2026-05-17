from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.approved:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed("Jūsu konts vēl nav apstiprināts. Lūdzu, gaidiet sava uzņēmuma CEO apstiprinājumu.")
        return data

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