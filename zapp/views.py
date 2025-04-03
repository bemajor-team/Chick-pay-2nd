from django.shortcuts import render ,redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import LoginForm
from django.views import View
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import MyPageSerializer, PasswordChangeSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Cash
from .serializers import CashSerializer, CashTransactionSerializer
from .forms import PasswordChangeForm 
from django.views import View
from .models import CashTransaction

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
            serializer.save()
            # 회원가입 성공 시 로그인 페이지로 리다이렉트
            return redirect('login')  # 'login'은 urls.py에서 지정한 name 값
        return render(request, 'register.html', {'form': serializer, 'errors': serializer.errors})


class LoginView(APIView):
    def get(self, request):
        return render(request, 'login.html', {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)  # ✅ 세션 로그인 처리
            return redirect('home')  # 로그인 후 이동할 페이지 이름
        return render(request, 'login.html', {"form": form, "errors": form.errors})


@method_decorator(login_required, name='dispatch')
class HomeView(APIView):
    def get(self, request):
        return render(request, 'home.html' )
        
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
                cash.deposit(amount)

                CashTransaction.objects.create(
                user=request.user,
                transaction_type='deposit',
                amount=amount,
                memo=request.data.get('memo', '')  # 선택사항
            )

        # ✅ 세션에 금액 저장해서 완료 페이지에서 표시할 수 있게
                request.session['last_deposit_amount'] = float(amount)

                return redirect('deposit-complete')

        if request.accepted_renderer.format == 'html':
                messages.error(request._request, "입금 금액이 올바르지 않습니다.")
                return redirect('cash-deposit')

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepositCompleteView(View):
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

            # ✅ 출금 시도
            success = cash.withdraw(amount)

            if not success:
                messages.error(request._request, "잔액이 부족합니다.")
                return redirect('cash-withdraw')

            # ✅ 출금 성공 후 거래 기록
            CashTransaction.objects.create(
                user=request.user,
                transaction_type='withdraw',
                amount=amount,
                memo=request.data.get('memo', '')
            )

            request.session['last_withdraw_amount'] = float(amount)
            return redirect('withdraw-complete')

        if request.accepted_renderer.format == 'html':
            messages.error(request._request, "출금 금액이 올바르지 않습니다.")
            return redirect('cash-withdraw')

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WithdrawCompleteView(View):
    def get(self, request):
        user = request.user
        
        cash = getattr(user, 'cash', None)

        recent_withdraws = CashTransaction.objects.filter(
            user=user,
            transaction_type='withdraw'
        ).order_by('-created_at')[:]

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



# class MyPageView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         user = request.user
#         cash = getattr(user, 'cash', None)
        
#         # Accept 헤더 확인
#         if request.accepted_renderer.format == 'json':
#             serializer = MyPageSerializer(request.user)
#             return Response(serializer.data)

#         # HTML 응답
#         context = {
#             'name': user.name,
#             'email': user.email,
#             'birthdate': user.birthdate,
#             'balance': cash.balance if cash else 0.00,
#         }
#         return render(request, 'mypage.html', context)

class CashTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        cash = getattr(user, 'cash', None)
        
        if request.accepted_renderer.format == 'json':
            serializer = MyPageSerializer(request.user)
            return Response(serializer.data)
        # HTML 응답
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
            # 금액 이체
            sender.cash.withdraw(amount)
            receiver.cash.deposit(amount)

            # 송금 기록 저장
            CashTransfer.objects.create(
                sender=sender,
                receiver=receiver,
                amount=amount,
                memo=memo
            )

            request.session['last_transfer_amount'] = float(amount)
            request.session['last_receiver_name'] = receiver.name
            return redirect('transfer-complete')
            
        except Exception as e:
            messages.error(request, "송금 처리 중 오류가 발생했습니다.")
            return redirect('transfer')


    # def post(self, request):
    #     serializer = TransferSerializer(data=request.data, context={'request': request})
    #     if serializer.is_valid():
    #         sender = request.user
    #         receiver_email = serializer.validated_data['receiver_email']
    #         amount = serializer.validated_data['amount']
    #         memo = serializer.validated_data.get('memo', '')

    #         try:
    #             receiver = CustomUser.objects.get(email=receiver_email)
    #         except CustomUser.DoesNotExist:
    #             messages.error(request._request, "받는 사람을 찾을 수 없습니다.")
    #             return redirect('transfer')

    #         # 금액 이체
    #         sender.cash.withdraw(amount)
    #         receiver.cash.deposit(amount)

    #         # 송금 기록 저장
    #         CashTransfer.objects.create(
    #             sender=sender,
    #             receiver=receiver,
    #             amount=amount,
    #             memo=memo
    #         )

    #         request.session['last_transfer_amount'] = float(amount)
    #         request.session['last_receiver_name'] = receiver.name
    #         return redirect('transfer-complete')

    #     messages.error(request._request, "송금 요청이 올바르지 않습니다.")
    #     return redirect('transfer')

