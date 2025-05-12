import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from zapp.models import CustomUser, Cash
import pyotp

@pytest.mark.django_db
def test_otp_verification():
    user = CustomUser.objects.create_user(
        email="otpuser@example.com", password="Pass1234", name="OTP유저"
    )
    Cash.objects.create(user=user, balance=0)

    # OTP 설정
    user.otp_secret = pyotp.random_base32()
    user.save()

    totp = pyotp.TOTP(user.otp_secret)
    otp_code = totp.now()

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(reverse('api-otp-verify'), {"otp_code": otp_code})
    assert response.status_code == 200
    assert response.data['message'] == "인증 성공"
