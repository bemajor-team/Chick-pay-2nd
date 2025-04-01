from rest_framework import serializers
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'birthdate', 'password']  # ✅ birthdate 추가

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            birthdate=validated_data.get('birthdate'),  # ✅ 생년월일 저장
            password=validated_data['password']
        )
        return user
