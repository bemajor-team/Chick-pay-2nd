from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from zapp.models import Cash, CashTransaction, CashTransfer, CustomUser
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import pyotp , json ,qrcode , base64
from io import BytesIO

@csrf_exempt
def health_check(request):
    return HttpResponse("ok")

class LoginRequired403Mixin(AccessMixin):
    """로그인 안 했으면 403 Forbidden 터뜨리는 Mixin"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied  # ✅ 403
        return super().dispatch(request, *args, **kwargs)

class OTPRequiredMixin:
    """OTP 인증 여부를 체크하는 Mixin (관리자는 OTP 면제)"""
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:  # ✅ superuser는 OTP 검사 건너뜀
            return super().dispatch(request, *args, **kwargs)

        if not request.session.get('otp_verified', False):
            return redirect('otp-setup')
        return super().dispatch(request, *args, **kwargs)

    
class MainTemplateView(TemplateView):
    template_name = 'main.html'

class RegisterTemplateView(TemplateView):
    template_name = 'register.html'

class LoginTemplateView(TemplateView):
    template_name = 'login.html'

class MyPageTemplateView(LoginRequired403Mixin, OTPRequiredMixin , TemplateView):
    template_name = 'mypage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cash = getattr(user, 'cash', None)

        context['name'] = user.name
        context['email'] = user.email
        context['birthdate'] = user.birthdate
        context['balance'] = cash.balance if cash else 0.00
        return context
    
class CashDepositTemplateView(LoginRequired403Mixin, OTPRequiredMixin, TemplateView):
    template_name = 'deposit.html'

class DepositCompleteTemplateView(LoginRequired403Mixin, OTPRequiredMixin, TemplateView):
    template_name = 'deposit-complete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cash = getattr(user, 'cash', None)
        
        # 최근 입금 내역 조회
        recent_deposits = CashTransaction.objects.filter(user=user, transaction_type='deposit').order_by('-created_at')
        
        # 최신 입금액과 이전 잔액 계산
        latest_amount = recent_deposits[0].amount if recent_deposits else 0
        previous_balance = cash.balance - latest_amount if cash else 0.00
        
        context['name'] = user.name
        context['email'] = user.email
        context['balance'] = cash.balance if cash else 0.00
        context['recent_deposits'] = recent_deposits
        context['previous_balance'] = previous_balance
        
        return context

class CashWithdrawTemplateView(LoginRequired403Mixin,OTPRequiredMixin, TemplateView):
    template_name = 'withdraw.html'


class WithdrawCompleteTemplateView(LoginRequired403Mixin,OTPRequiredMixin, TemplateView):
    template_name = 'withdraw-complete.html'  # ✅ template_name 명시

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cash = getattr(user, 'cash', None)

        # 최근 출금 내역 조회
        recent_withdraws = CashTransaction.objects.filter(
            user=user,
            transaction_type='withdraw'
        ).order_by('-created_at')

        # 최신 출금액과 이전 잔액 계산
        latest_amount = recent_withdraws[0].amount if recent_withdraws else 0
        previous_balance = cash.balance + latest_amount if cash else 0.00

        context['name'] = user.name
        context['email'] = user.email
        context['balance'] = cash.balance if cash else 0.00
        context['recent_withdraws'] = recent_withdraws
        context['previous_balance'] = previous_balance

        return context

class CashTransferTemplateView(LoginRequired403Mixin, OTPRequiredMixin, TemplateView):
    template_name = 'transfer.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context.update({
            'name': user.name,
            'email': user.email
        })
        return context

class TransferCompleteTemplateView(LoginRequired403Mixin,OTPRequiredMixin, TemplateView):
    template_name = 'transfer-complete.html'  # ✅ template_name 명시

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        transfer = CashTransfer.objects.filter(sender=user).order_by('-created_at').first()

        context.update({
            'sender_email': user.email,
            'receiver_email': transfer.receiver.email if transfer else '',
            'receiver_name': transfer.receiver.name if transfer else '',
            'amount': transfer.amount if transfer else 0.00,
            'memo': transfer.memo if transfer else '',
            'created_at': transfer.created_at if transfer else None,
        })

        return context

class AllTransactionTemplateView(LoginRequired403Mixin, OTPRequiredMixin,TemplateView):
    template_name = 'account.html'  # ✅ template_name 명시

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cash = getattr(user, 'cash', None)

        transaction_list = CashTransaction.objects.filter(user=user).order_by('-created_at')
        paginator = Paginator(transaction_list, 5)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context.update({
            'transactions': page_obj,
            'name': user.name,
            'email': user.email,
            'balance': cash.balance if cash else 0.00,
            'page_obj': page_obj,
        })

        return context

class UnregisterTemplateView(LoginRequired403Mixin,OTPRequiredMixin, TemplateView):
    template_name = 'unregister.html'


# ✅ 실제 동작용 View (웹 페이지 렌더링)
class OTPSetupTemplateView(LoginRequired403Mixin, TemplateView):
    template_name = 'otp_setup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not hasattr(user, 'otp_secret') or not user.otp_secret:
            user.otp_secret = pyotp.random_base32()
            user.save()

        totp = pyotp.TOTP(user.otp_secret)
        otp_uri = totp.provisioning_uri(name=user.email, issuer_name="CHICKPAY")

        qr = qrcode.make(otp_uri)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        context.update({
            'otp_secret': user.otp_secret,
            'qr_code_url': f'data:image/png;base64,{qr_base64}',
        })

        return context


def custom_403_view(request, exception=None):
    return render(request, '403.html', status=403)


#bandit report
def bandit_report_view(request):
    with open("analysis/bandit-report.json") as f:
        data = json.load(f)

    context = {
        "issues": data.get("results", []),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return render(request, "bandit_report.html", context)
