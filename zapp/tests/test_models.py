import pytest
from zapp.models import CustomUser, Cash

@pytest.mark.django_db
def test_user_creation():
    user = CustomUser.objects.create_user(
        email="user@example.com", password="Strongpass123", name="테스터"
    )
    assert user.email == "user@example.com"
    assert user.check_password("Strongpass123")

@pytest.mark.django_db
def test_cash_deposit_withdraw():
    user = CustomUser.objects.create_user(
        email="cash@example.com", password="Strongpass123", name="캐시테스터"
    )
    cash = Cash.objects.create(user=user, balance=1000)

    cash.deposit(500)
    assert cash.balance == 1500

    assert cash.withdraw(700)
    assert cash.balance == 800

    assert not cash.withdraw(2000)  # 잔액 부족
    assert cash.balance == 800
