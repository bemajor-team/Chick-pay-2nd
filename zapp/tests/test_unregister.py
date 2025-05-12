import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from zapp.models import CustomUser, Cash

@pytest.mark.django_db
def test_unregister():
    user = CustomUser.objects.create_user(
        email="deleteuser@example.com", password="Pass1234", name="탈퇴유저"
    )
    Cash.objects.create(user=user, balance=0)

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.delete(
        reverse('api-unregister'),
        {"password": "Pass1234"},
        format='json'
    )
    assert response.status_code == 204
