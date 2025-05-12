import re
from rest_framework import serializers
from django.contrib.auth import get_user_model , password_validation
from .models import CustomUser, Cash


#로그인 시리얼라이저
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    

    def validate(self, data):
        from django.contrib.auth import authenticate

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError("이메일과 비밀번호를 모두 입력하세요.")

        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError("이메일 또는 비밀번호가 틀렸습니다.")

        if not user.is_active:
            raise serializers.ValidationError("비활성화된 계정입니다.")

        data['user'] = user
        return data

# 🔐 회원가입 Serializer 이거 쓰임
class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

  

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'birthdate', 'password1', 'password2']

        extra_kwargs = {
            'email': {
                'validators': []  # ✅ unique 검사 끄기
            }
        }

    def validate_email(self, value):
        """이메일 포맷 + 중복검사 + 사용자 에러 메시지"""
        if '@' not in value:
            raise serializers.ValidationError("유효한 이메일 주소를 입력하세요.")
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")  # 🔥 문구 커스텀
        return value


    def validate_name(self, value):
        """이름: 한글/영어만 허용"""
        if not re.match(r'^[가-힣a-zA-Z]+$', value):
            raise serializers.ValidationError("이름은 한글과 영어만 사용할 수 있습니다.")
        return value

    def validate_birthdate(self, value):
        """생년월일: 과거 날짜만 허용"""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("생년월일은 미래일 수 없습니다.")
        return value

    def validate(self, data):
        """패스워드 두 개 일치 + 패스워드 복잡성 검증"""
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password2": "비밀번호가 일치하지 않습니다."})

        password = data['password1']
    
        if len(password) < 8:
            raise serializers.ValidationError({"password1": "비밀번호는 최소 8자 이상이어야 합니다."})
        if not re.search(r'[A-Z]', password):
            raise serializers.ValidationError({"password1": "비밀번호에 대문자가 포함되어야 합니다."})
        if not re.search(r'[a-z]', password):
            raise serializers.ValidationError({"password1": "비밀번호에 소문자가 포함되어야 합니다."})
        if not re.search(r'\d', password):
            raise serializers.ValidationError({"password1": "비밀번호에 숫자가 포함되어야 합니다."})

        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password1')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user


# 💰 캐시 정보 Serializer (조회용)
# class CashSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source='user.email', read_only=True)

#     class Meta:
#         model = Cash
#         fields = ['name', 'user', 'email', 'balance', 'created_at', 'updated_at']
#         read_only_fields = ['nane' ,'user', 'email', 'balance', 'created_at', 'updated_at']

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

# 💸 캐시 충전/사용 Serializer 이거 쓰임
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


#쓰임
class TransferSerializer(serializers.Serializer):
    receiver_email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    memo = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        request = self.context['request']
        sender = request.user

        # 1. 본인에게 송금 불가
        if sender.email == data['receiver_email']:
            raise serializers.ValidationError({"receiver_email": "자기 자신에게 송금할 수 없습니다."})

        # 2. 받는 사람 존재 여부
        try:
            receiver = CustomUser.objects.get(email=data['receiver_email'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"receiver_email": "받는 사람을 찾을 수 없습니다."})

        # 3. 송금액 > 0
        if data['amount'] <= 0:
            raise serializers.ValidationError({"amount": "송금액은 0보다 커야 합니다."})

        # 4. 잔액 부족
        if sender.cash.balance < data['amount']:
            raise serializers.ValidationError({"amount": "잔액이 부족합니다."})

        return data


class UnregisterPasswordCheckSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        return value
