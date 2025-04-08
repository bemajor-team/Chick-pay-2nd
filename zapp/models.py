from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db import models
from django.conf import settings  # AUTH_USER_MODEL을 사용하기 위해

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수입니다.")
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    birthdate = models.DateField(null=True, blank=True)  # ✅ 생년월일 추가!
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = CustomUserManager()
    otp_secret = models.CharField(max_length=32, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email


class Cash(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,  # user_id가 cash의 PK가 됨
        related_name='cash'  # request.user.cash 로 접근 가능
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def deposit(self, amount):
        self.balance += amount
        self.save()

    def withdraw(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.save()

            return True
        return False

    def __str__(self):
        return f"{self.user.email} - Balance: {self.balance}"

class CashTransfer(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_transfers')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_transfers')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    memo = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.email} → {self.receiver.email}: {self.amount}원"



class CashTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', '입금'),
        ('withdraw', '출금'),
        ('transfer', '송금'),  # ✅ 튜플 형식!
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    memo = models.CharField(max_length=255, blank=True, null=True)
    related_transfer = models.ForeignKey(
        'CashTransfer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_transaction_type_display()}] {self.user.name} - {self.amount}원"

