import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from zapp.models import CustomUser, Cash


#fixture = 테스트 함수에 데이터를 제공하는 헬퍼(보조) 역할
@pytest.fixture
def user_with_cash(db):
    user = CustomUser.objects.create_user(
        email="cashuser@example.com", password="Testpass123", name="캐시유저"
    )
    Cash.objects.create(user=user, balance=10000)
    return user

@pytest.mark.django_db
def test_cash_deposit(user_with_cash):
    client = APIClient()
    client.force_authenticate(user=user_with_cash)

    response = client.post(reverse('api-cash-deposit'), {"amount": 5000})
    assert response.status_code == 200
    assert response.data['balance'] == 15000

@pytest.mark.django_db
def test_cash_withdraw(user_with_cash):
    client = APIClient()
    client.force_authenticate(user=user_with_cash)

    response = client.post(reverse('api-cash-withdraw'), {"amount": 4000})
    assert response.status_code == 200
    assert response.data['balance'] == 6000
