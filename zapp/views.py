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




class MainView(APIView):
    def get(self, request):
        # 메인 페이지로 HTML을 렌더링한다.
        return render(request, 'main.html')
    
class RegisterView(APIView):
    def get(self, request):
        # 그냥 render() 함수로 HTML 파일을 반환
        return render(request, 'register.html')
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "회원가입 성공!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        