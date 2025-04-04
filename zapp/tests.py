
#python manage.py test zapp.tests.<class이름>

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from zapp.models import Cash, CashTransaction, CashTransfer  # ← 앱 이름 맞게 수정

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


from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from zapp.models import Cash, CashTransaction, CashTransfer  # 앱 이름에 맞게 수정

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

