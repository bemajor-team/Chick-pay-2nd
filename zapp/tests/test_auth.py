import pytest
from django.urls import reverse
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_register_and_login():
    client = APIClient()

    # 회원가입
    data = {
        "email": "testuser@example.com",
        "name": "SignupTester", 
        "birthdate": "1995-01-01",
        "password1": "StrongPass1",
        "password2": "StrongPass1"
    }
    response = client.post(reverse('api-register'), data, format='json')
    print("회원가입 response data:", response.data)  # ✅ 추가!!
    assert response.status_code == 201

    # 로그인
    response = client.post(reverse('api-login'), {
        "email": "testuser@example.com",
        "password": "StrongPass1"
    }, format='json')
    assert response.status_code == 200
    assert response.data['message'] == "로그인 성공!"
