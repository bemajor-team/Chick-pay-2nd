from rest_framework import serializers
from django.contrib.auth import get_user_model , password_validation
from .models import CustomUser, Cash

User = get_user_model()  # 이 부분 추가
# 🔐 회원가입 Serializer
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

# 💰 캐시 정보 Serializer (조회용)
class CashSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Cash
        fields = ['name', 'user', 'email', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['nane' ,'user', 'email', 'balance', 'created_at', 'updated_at']

# 🔐 비밀번호 변경 Serializer
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({'old_password': '기존 비밀번호가 틀렸습니다.'})
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

# 💸 캐시 충전/사용 Serializer
class CashTransactionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("금액은 0보다 커야 합니다.")
        return value


# 👤 마이페이지 정보 조회 Serializer
class MyPageSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(
        source='cash.balance',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'birthdate', 'balance']

class TransferSerializer(serializers.Serializer):
    receiver_email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    memo = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("송금액은 0보다 커야 합니다.")
        
        user = self.context['request'].user
        if user.cash.balance < value:
            raise serializers.ValidationError("잔액이 부족합니다.")
        return value

    def validate_receiver_email(self, value):
        user = self.context['request'].user
        if user.email == value:
            raise serializers.ValidationError("자신에게는 송금할 수 없습니다.")
        
        try:
            CustomUser.objects.get(email=value)  # User 대신 CustomUser 사용
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 사용자입니다.")
            
        return value

