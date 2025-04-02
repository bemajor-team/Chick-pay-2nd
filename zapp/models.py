from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings  # AUTH_USER_MODEL을 사용하기 위해

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수입니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    birthdate = models.DateField(null=True, blank=True)  # ✅ 생년월일 추가!
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

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




# class Cash(models.Model):
#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL,  # CustomUser 모델과 연결
#         on_delete=models.CASCADE,
#         related_name='cash'  
#     )
#     balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def deposit(self, amount):
#         self.balance += amount
#         self.save()

#     def withdraw(self, amount):
#         if self.balance >= amount:
#             self.balance -= amount
#             self.save()
#             return True
#         return False

#     def __str__(self):
#         return f"{self.user.email} - Balance: {self.balance}"


# class Cash(models.Model):
#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         primary_key=True,  # ✅ user_id를 이 테이블의 PK로 설정
#         related_name='cash'
#     )
#     balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def deposit(self, amount):
#         self.balance += amount
#         self.save()

#     def withdraw(self, amount):
#         if self.balance >= amount:
#             self.balance -= amount
#             self.save()
#             return True
#         return False

#     def __str__(self):
#         return f"{self.user.email} - Balance: {self.balance}"