import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from zapp.models import CustomUser, Cash

@pytest.mark.django_db
def test_cash_transfer():
    sender = CustomUser.objects.create_user(
        email="sender@example.com", password="Pass1234", name="보내는사람"
    )
    receiver = CustomUser.objects.create_user(
        email="receiver@example.com", password="Pass1234", name="받는사람"
    )

    Cash.objects.create(user=sender, balance=10000)
    Cash.objects.create(user=receiver, balance=1000)

    client = APIClient()
    client.force_authenticate(user=sender)

    data = {
        "receiver_email": "receiver@example.com",
        "amount": 5000,
        "memo": "테스트송금"
    }

    response = client.post(reverse('api-cash-transfer'), data)
    assert response.status_code == 200

    sender.refresh_from_db()
    receiver.refresh_from_db()

    assert sender.cash.balance == 5000
    assert receiver.cash.balance == 6000
