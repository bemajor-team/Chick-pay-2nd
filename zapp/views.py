from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.views import View
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status 
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from django.shortcuts import render


from .forms import LoginForm, PasswordChangeForm
from .models import Cash, CashTransaction, CustomUser, CashTransfer
from .serializers import (
    RegisterSerializer,
    MyPageSerializer,
    CashSerializer,
    CashTransactionSerializer,
    TransferSerializer,
)

from django.db import transaction

import pyotp
import qrcode
import base64
from io import BytesIO

class MainView(APIView):
    def get(self, request):
        # 메인 페이지로 HTMlaL을 렌더링한다.
        return render(request, 'main.html')

class RegisterView(APIView):
    def get(self, request):
        return render(request, 'register.html')


    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # 회원가입 시 Cash 객체 생성
            Cash.objects.create(user=user, balance=0)
            return redirect('login')
        return render(request, 'register.html', {'form': serializer, 'errors': serializer.errors})

    # def post(self, request):
    #     serializer = RegisterSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         # 회원가입 성공 시 로그인 페이지로 리다이렉트
    #         return redirect('login')  # 'login'은 urls.py에서 지정한 name 값
    #     return render(request, 'register.html', {'form': serializer, 'errors': serializer.errors})

class LoginView(APIView):
    def get(self, request):
        return render(request, 'login.html', {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)  # ✅ 세션 로그인 처리
            return redirect('otp-setup')  # 로그인 후 이동할 페이지 이름
        return render(request, 'login.html', {"form": form, "errors": form.errors})

class MyPageView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        cash = getattr(user, 'cash', None)
        
        # Accept 헤더 확인
        if request.accepted_renderer.format == 'json':
            serializer = MyPageSerializer(request.user)
            return Response(serializer.data)

        # HTML 응답
        context = {
            'name': user.name,
            'email': user.email,
            'birthdate': user.birthdate,
            'balance': cash.balance if cash else 0.00,
        }
        return render(request, 'mypage.html', context)
    
class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        form = PasswordChangeForm(request.data)
        
        if form.is_valid():
            user = request.user
            current_password = form.cleaned_data['current_password']
            new_password = form.cleaned_data['new_password']

            if not user.check_password(current_password):
                return render(request, 'change_password.html', {
                    'form': form,
                    'error': "현재 비밀번호가 일치하지 않습니다."
                })

            user.set_password(new_password)
            user.save()
            
            # 비밀번호 변경 성공 시 로그인 페이지로 리다이렉트
            return redirect('login')
            
            
        return render(request, 'change_password.html', {
            'form': form,
            'errors': form.errors
        })


class CashDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cash, created = Cash.objects.get_or_create(user=request.user)
        serializer = CashSerializer(cash)
        return Response(serializer.data)


class CashDepositView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(request, 'deposit.html')

    def post(self, request):
        cash, _ = Cash.objects.get_or_create(user=request.user)
        serializer = CashTransactionSerializer(data=request.data)

        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            try:
                with transaction.atomic():  # ✅ 트랜잭션 시작
                    cash.deposit(amount)

                    CashTransaction.objects.create(
                        user=request.user,
                        transaction_type='deposit',
                        amount=amount,
                        memo=request.data.get('memo', '')  # 선택사항
                    )

                # 성공 시 세션에 저장
                request.session['last_deposit_amount'] = float(amount)
                return redirect('deposit-complete')

            except Exception as e:
                messages.error(request._request, "입금 처리 중 오류가 발생했습니다.")
                return redirect('cash-deposit')

        if request.accepted_renderer.format == 'html':
            messages.error(request._request, "입금 금액이 올바르지 않습니다.")
            return redirect('cash-deposit')

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class DepositCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        cash = getattr(user, 'cash', None)

        recent_deposits = CashTransaction.objects.filter(
            user=user,
            transaction_type='deposit'
        ).order_by('-created_at')[:]

        if recent_deposits:
            latest_deposit_amount = recent_deposits[0].amount
                   
            previous_balance = cash.balance - latest_deposit_amount
        
        context = {
            'name': user.name,
            'email': user.email,
            'balance': cash.balance if cash else 0.00,
            'recent_deposits': recent_deposits,
            'previous_balance' : previous_balance,
            
        }

        return render(request, 'deposit-complete.html', context)


class CashWithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(request, 'withdraw.html')

    def post(self, request):
        cash, _ = Cash.objects.get_or_create(user=request.user)
        serializer = CashTransactionSerializer(data=request.data)

        if serializer.is_valid():
            amount = serializer.validated_data['amount']

            try:
                with transaction.atomic():  # ✅ 트랜잭션 시작
                    success = cash.withdraw(amount)

                    if not success:
                        # 트랜잭션 내에서 실패하면 rollback 됨
                        messages.error(request._request, "잔액이 부족합니다.")
                        raise Exception("잔액 부족")

                    CashTransaction.objects.create(
                        user=request.user,
                        transaction_type='withdraw',
                        amount=amount,
                        memo=request.data.get('memo', '')
                    )

                # 성공 시 세션 저장 및 리디렉션
                request.session['last_withdraw_amount'] = float(amount)
                return redirect('withdraw-complete')

            except Exception:
                # 트랜잭션 전체가 롤백됨
                return redirect('cash-withdraw')

        if request.accepted_renderer.format == 'html':
            messages.error(request._request, "출금 금액이 올바르지 않습니다.")
            return redirect('cash-withdraw')

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WithdrawCompleteView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        
        cash = getattr(user, 'cash', None)

        recent_withdraws = CashTransaction.objects.filter(
            user=user,
            transaction_type='withdraw'
        ).order_by('-created_at')[:]

        previous_balance = None

        if recent_withdraws:
            latest_withdraw_amount = recent_withdraws[0].amount
                   
            previous_balance = cash.balance + latest_withdraw_amount
        
        context = {
            'name': user.name,
            'email': user.email,
            'balance': cash.balance if cash else 0.00,
            'recent_withdraws': recent_withdraws,
            'previous_balance' : previous_balance,
            
        }

        return render(request, 'withdraw-complete.html', context)
class CashTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        cash = getattr(user, 'cash', None)

        if request.accepted_renderer.format == 'json':
            serializer = MyPageSerializer(request.user)
            return Response(serializer.data)

        context = {
            'name': user.name,
            'email': user.email,
        }
        return render(request, 'transfer.html', context)

    def post(self, request):
        data = {
            'receiver_email': request.POST.get('receiver_email'),
            'amount': request.POST.get('amount'),
            'memo': request.POST.get('memo', '')
        }

        serializer = TransferSerializer(data=data, context={'request': request})
        if not serializer.is_valid():
            for error in serializer.errors.values():
                messages.error(request, error[0])
            return redirect('transfer')

        sender = request.user
        receiver_email = serializer.validated_data['receiver_email']
        amount = serializer.validated_data['amount']
        memo = serializer.validated_data.get('memo', '')

        try:
            receiver = CustomUser.objects.get(email=receiver_email)
        except CustomUser.DoesNotExist:
            messages.error(request, "받는 사람을 찾을 수 없습니다.")
            return redirect('transfer')

        try:
            with transaction.atomic():  # ✅ 트랜잭션 블록 시작
                # 출금
                if not sender.cash.withdraw(amount):
                    messages.error(request._request, "잔액이 부족합니다.")
                    raise Exception("잔액 부족")

                # 입금
                receiver.cash.deposit(amount)

                # 송금 기록
                transfer = CashTransfer.objects.create(
                    sender=sender,
                    receiver=receiver,
                    amount=amount,
                    memo=memo
                )

                # 거래 기록 (보내는 사람)
                CashTransaction.objects.create(
                    user=sender,
                    transaction_type='transfer',
                    amount=amount,
                    memo=f"{receiver.email}님에게 송금",
                    related_transfer=transfer
                )

                # 거래 기록 (받는 사람)
                CashTransaction.objects.create(
                    user=receiver,
                    transaction_type='deposit',
                    amount=amount,
                    memo=f"{sender.email}로부터 입금",
                    related_transfer=transfer
                )

            # ✅ 트랜잭션 성공 시 세션에 정보 저장
            request.session['last_transfer_amount'] = float(amount)
            request.session['last_receiver_name'] = receiver.name
            return redirect('transfer-complete')

        except Exception as e:
            print(f"송금 처리 중 오류 발생: {str(e)}")  # 디버깅용
            messages.error(request, "송금 처리 중 오류가 발생했습니다.")
            return redirect('transfer')


class TransferCompleteView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user

        # 최근 송금 내역 1건 (CashTransfer에서)
        latest_transfer = CashTransfer.objects.filter(sender=user).order_by('-created_at').first()

        context = {
            'sender_email': user.email,
            'receiver_email': latest_transfer.receiver.email if latest_transfer else '',
            'receiver_name': latest_transfer.receiver.name if latest_transfer else '',
            'amount': latest_transfer.amount if latest_transfer else 0.00,
            'memo': latest_transfer.memo if latest_transfer and latest_transfer.memo else '',
            'created_at': latest_transfer.created_at if latest_transfer else None, 
        }

        return render(request, 'transfer-complete.html', context)
    
class AllTransactionView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        cash = getattr(user, 'cash', None)

        # 전체 거래 내역 최신순
        transaction_list = CashTransaction.objects.filter(user=user).order_by('-created_at')

        # ✅ 페이지네이션 처리: 한 페이지에 5개씩
        paginator = Paginator(transaction_list, 5)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            'transactions': page_obj,  # 페이징된 거래 목록
            'name': user.name,
            'email': user.email,
            'balance': cash.balance if cash else 0.00,
            'page_obj': page_obj,  # 템플릿에서 페이지네이션 정보에 사용
        }

        return render(request, 'account.html', context)
    


# ✅ 실제 동작용 View (웹 페이지 렌더링)
def otp_setup(request):
    user = request.user

    if not user.is_authenticated:
        raise PermissionDenied

    if not hasattr(user, 'otp_secret') or not user.otp_secret:
        user.otp_secret = pyotp.random_base32()
        user.save()

    totp = pyotp.TOTP(user.otp_secret)
    otp_uri = totp.provisioning_uri(name=user.email, issuer_name="CHICKPAY")

    qr = qrcode.make(otp_uri)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        if totp.verify(otp_code):
            return redirect('main')
        else:
            return render(request, 'otp_setup.html', {
                'otp_secret': user.otp_secret,
                'qr_code_url': f'data:image/png;base64,{qr_base64}',
                'error': 'OTP 인증 실패!'
            })

    return render(request, 'otp_setup.html', {
        'otp_secret': user.otp_secret,
        'qr_code_url': f'data:image/png;base64,{qr_base64}'
    })

def custom_403_view(request, exception=None):
    return render(request, '403.html', status=403)

