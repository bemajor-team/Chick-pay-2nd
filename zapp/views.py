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
        

# zapp/views.py


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

        transactions = CashTransaction.objects.filter(user=user).order_by('-created_at')  # 최신순

        context = {
            'name': user.name,
            'email': user.email,
            'balance': cash.balance if cash else 0.00

    
        }

        return render(request, 'deposit-complete.html', context)

class CashWithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cash, created = Cash.objects.get_or_create(user=request.user)
        serializer = CashTransactionSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            if cash.withdraw(amount):
                return Response({'message': f"{amount}원이 출금되었습니다.", 'balance': cash.balance})
            else:
                return Response({'error': '잔액이 부족합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# error패스워드

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


# class PasswordChangeView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             # ✅ 메시지 추가 (선택)
#             messages.success(request._request, "비밀번호가 변경되었습니다.")
#             return redirect('mypage')  # mypage URL로 이동
#         # ❌ 실패 시도: 템플릿 없이 Response() 사용
#         # => 여기서도 렌더링해줄 템플릿 필요하거나, 리다이렉트
#         messages.error(request._request, "비밀번호 변경에 실패했습니다.")
#         return redirect('mypage')  # 실패 시도 동일한 페이지로

# 🔐 비밀번호 변경

# class PasswordChangeView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response({'message': '비밀번호가 변경되었습니다.'})
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# # 👤 마이페이지 정보 조회
# class MyPageView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         # 브라우저에서 보통 HTML을 원할 때 Accept 헤더가 아래처럼 오기 때문에
#         accept = request.META.get('HTTP_ACCEPT', '')

#         if 'application/json' in accept:
#             # 🔁 JSON 응답 (API 요청)
#             serializer = MyPageSerializer(request.user)
#             return Response(serializer.data)

#         # 🖼️ 템플릿 렌더링 (브라우저 요청)
#         user = request.user
#         cash = getattr(user, 'cash', None)

#         context = {
#             'name': user.name,
#             'email': user.email,
#             'birthdate': user.birthdate,
#             'balance': cash.balance if cash else 0.00,
#         }

#         return render(request, 'mypage.html', context)


# class MyPageView(APIView):
#     permission_classes = [IsAuthenticated]
#     renderer_classes = [JSONRenderer, TemplateHTMLRenderer]

#     def get(self, request, *args, **kwargs):
#         if request.accepted_renderer.format == 'html':
#             # 🖼️ HTML 템플릿 렌더링
#             user = request.user
#             cash = getattr(user, 'cash', None)

#             context = {
#                 'name': user.name,
#                 'email': user.email,
#                 'birthdate': user.birthdate,
#                 'balance': cash.balance if cash else 0.00,
#             }

#             return Response(context, template_name='mypage.html')

#         # 🔁 JSON API 응답
#         serializer = MyPageSerializer(request.user)
#         return Response(serializer.data)


