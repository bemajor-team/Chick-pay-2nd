
#python manage.py test zapp.tests.<class이름>

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from zapp.models import Cash, CashTransaction, CashTransfer  # ← 앱 이름 맞게 수정
import pyotp
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from base64 import b64decode
from io import BytesIO
from PIL import Image
import pyotp
from django.test import TestCase, Client
from django.urls import reverse
from zapp.models import CustomUser
from django.contrib.auth.forms import AuthenticationForm
from zapp.forms import LoginForm
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from zapp.models import Cash, CashTransaction, CashTransfer  # 앱 이름에 맞게 수정


User = get_user_model()
class CashWithdrawTransactionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.cash = Cash.objects.create(user=self.user, balance=100.00)  # 💰 초기 잔고

    def test_withdraw_success(self):
        initial_balance = self.cash.balance
        amount = 40.00  # ✅ 잔고보다 작은 금액

        with transaction.atomic():
            success = self.cash.withdraw(amount)

            self.assertTrue(success, "출금이 성공해야 합니다.")

            CashTransaction.objects.create(
                user=self.user,
                transaction_type='withdraw',
                amount=amount,
                memo='성공 출금 테스트'
            )

        # 🔄 DB 새로고침
        self.cash.refresh_from_db()
        transaction_qs = CashTransaction.objects.filter(user=self.user, transaction_type='withdraw')

        # ✅ 잔고가 정확히 차감됐는지 확인
        self.assertEqual(self.cash.balance, initial_balance - amount)

        # ✅ 거래 내역 1개 생성 확인
        self.assertEqual(transaction_qs.count(), 1)
        txn = transaction_qs.first()
        self.assertEqual(txn.amount, amount)
        self.assertEqual(txn.memo, '성공 출금 테스트')




User = get_user_model()

class CashTransferTest(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(email='sender@test.com', password='testpass')
        self.receiver = User.objects.create_user(email='receiver@test.com', password='testpass')

        self.sender_cash = Cash.objects.create(user=self.sender, balance=50.00)  # 💸 잔액 부족한 금액
        self.receiver_cash = Cash.objects.create(user=self.receiver, balance=100.00)

    def test_transfer_fails_when_insufficient_balance(self):
        initial_sender_balance = self.sender_cash.balance
        initial_receiver_balance = self.receiver_cash.balance
        amount = 100.00  # ⛔ 잔액보다 큰 금액

        try:
            with transaction.atomic():
                # 출금 실패 유도
                success = self.sender_cash.withdraw(amount)
                if not success:
                    raise Exception("잔액 부족")

                # 정상적인 흐름이라면 아래 코드들은 실행 안 됨
                self.receiver_cash.deposit(amount)

                transfer = CashTransfer.objects.create(
                    sender=self.sender,
                    receiver=self.receiver,
                    amount=amount,
                    memo='테스트 송금'
                )

                CashTransaction.objects.create(
                    user=self.sender,
                    transaction_type='transfer',
                    amount=amount,
                    memo='테스트',
                    related_transfer=transfer
                )

                CashTransaction.objects.create(
                    user=self.receiver,
                    transaction_type='deposit',
                    amount=amount,
                    memo='테스트',
                    related_transfer=transfer
                )

        except:
            pass  # 트랜잭션 롤백 후 상태 확인

        # ✅ DB 새로고침
        self.sender_cash.refresh_from_db()
        self.receiver_cash.refresh_from_db()

        # ✅ 트랜잭션 롤백 확인
        self.assertEqual(self.sender_cash.balance, initial_sender_balance)
        self.assertEqual(self.receiver_cash.balance, initial_receiver_balance)

        self.assertEqual(CashTransfer.objects.count(), 0)
        self.assertEqual(CashTransaction.objects.count(), 0)

User = get_user_model()

class CashTransferSuccessTest(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(email='sender@test.com', password='testpass')
        self.receiver = User.objects.create_user(email='receiver@test.com', password='testpass')

        self.sender_cash = Cash.objects.create(user=self.sender, balance=200.00)
        self.receiver_cash = Cash.objects.create(user=self.receiver, balance=50.00)

    def test_successful_transfer_creates_all_records(self):
        send_amount = 100.00
        initial_sender_balance = self.sender_cash.balance
        initial_receiver_balance = self.receiver_cash.balance

        with transaction.atomic():
            # 출금
            success = self.sender_cash.withdraw(send_amount)
            self.assertTrue(success)

            # 입금
            self.receiver_cash.deposit(send_amount)

            # 송금 기록
            transfer = CashTransfer.objects.create(
                sender=self.sender,
                receiver=self.receiver,
                amount=send_amount,
                memo="성공 송금"
            )

            # 거래 기록
            CashTransaction.objects.create(
                user=self.sender,
                transaction_type='transfer',
                amount=send_amount,
                memo=f"{self.receiver.email}님에게 송금",
                related_transfer=transfer
            )

            CashTransaction.objects.create(
                user=self.receiver,
                transaction_type='deposit',
                amount=send_amount,
                memo=f"{self.sender.email}로부터 입금",
                related_transfer=transfer
            )

        # DB 새로고침
        self.sender_cash.refresh_from_db()
        self.receiver_cash.refresh_from_db()

        # ✅ 잔고 확인
        self.assertEqual(self.sender_cash.balance, initial_sender_balance - send_amount)
        self.assertEqual(self.receiver_cash.balance, initial_receiver_balance + send_amount)

        # ✅ 송금 기록 1개
        self.assertEqual(CashTransfer.objects.count(), 1)

        # ✅ 거래 기록 2개 (보낸 사람, 받은 사람)
        self.assertEqual(CashTransaction.objects.count(), 2)

        sender_txn = CashTransaction.objects.filter(user=self.sender).first()
        receiver_txn = CashTransaction.objects.filter(user=self.receiver).first()

        self.assertEqual(sender_txn.related_transfer, transfer)
        self.assertEqual(receiver_txn.related_transfer, transfer)

User = get_user_model()

class OTPSetupViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com', password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')
        self.url = reverse('otp-setup')  # URL 이름에 맞게 변경

    def test_get_request_generates_qr_and_secret(self):
        response = self.client.get(self.url)
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertIn('qr_code_url', response.context)
        self.assertIn('otp_secret', response.context)
        self.assertIsNotNone(self.user.otp_secret)

        # QR 이미지가 base64로 올바르게 생성되었는지 확인
        base64_img = response.context['qr_code_url'].split(',')[1]
        img_bytes = b64decode(base64_img)
        img = Image.open(BytesIO(img_bytes))
        self.assertEqual(img.format, 'PNG')

    def test_post_request_valid_otp(self):
        self.user.otp_secret = pyotp.random_base32()
        self.user.save()

        totp = pyotp.TOTP(self.user.otp_secret)
        valid_code = totp.now()

        response = self.client.post(self.url, {'otp_code': valid_code})
        self.assertEqual(response.status_code, 302)  # Redirect to 'main'

    def test_post_request_invalid_otp(self):
        self.user.otp_secret = pyotp.random_base32()
        self.user.save()

        invalid_code = '123456'  # 틀린 코드

        response = self.client.post(self.url, {'otp_code': invalid_code})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'OTP 인증 실패!')
        self.assertIn('qr_code_url', response.context)



class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User',
            birthdate=date(1990, 1, 1),
            # otp_secret='JBSWY3DPEHPK3PXP'
        )

        self.login_url = reverse('login')

    def test_login_page_GET(self):
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertIsInstance(response.context['form'], LoginForm)

    def test_login_fail_POST(self):
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_empty_POST(self):
        response = self.client.post(self.login_url, {})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertTrue(response.context['form'].errors)

    def test_create_user_without_email(self):
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(
                email='',
                password='test123',
                name='Test User'
            )
