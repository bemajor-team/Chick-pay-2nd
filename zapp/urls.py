from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', MainView.as_view(), name='main'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    # path('home/', HomeView.as_view(), name='home'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('mypage/', MyPageView.as_view(), name='mypage'),
    path('mypage/change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('cash/', CashDetailView.as_view(), name='cash-detail'),
    path('cash/deposit/complete/', DepositCompleteView.as_view(), name='deposit-complete'),
    path('cash/deposit/', CashDepositView.as_view(), name='cash-deposit'),
    path('cash/withdraw/', CashWithdrawView.as_view(), name='cash-withdraw'),
    path('cash/withdraw/complete', WithdrawCompleteView.as_view(), name='withdraw-complete'),
    path('cash/transfer/', CashTransferView.as_view(), name='cash-transfer'),
    path('cash/transfer/complete', TransferCompleteView.as_view(), name='transfer-complete'),
    path('account/', AllTransactionView.as_view(), name='account'),
    path('otp/setup/', otp_setup, name='otp-setup')
]
