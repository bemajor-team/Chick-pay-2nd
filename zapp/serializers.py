from rest_framework import serializers
from .models import CustomUser
from .models import Cash



class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'birthdate', 'password1', 'password2']

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')  # 확인용 비밀번호 제거
        password = validated_data.pop('password1')
        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )
        return user

# zapp/serializers.py

from rest_framework import serializers
from .models import Cash

class CashSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Cash
        fields = ['user', 'email', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['user', 'email', 'created_at', 'updated_at', 'balance']

class CashTransactionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("금액은 0보다 커야 합니다.")
        return value
