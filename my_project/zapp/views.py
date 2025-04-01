from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from .serializers import RegisterSerializer
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

# class RegisterView(APIView):
#     def get(self, request):
#         return render(request, 'register.html')
    
#     def post(self, request):
#         serializer = RegisterSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "회원가입 성공!"}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# class RegisterView(APIView):
#     def get(self, request):
#         # Django의 render()를 사용하지 않고 Response로 HTML 템플릿을 반환하도록 수정
#         return Response(render(request, 'register.html').content, content_type='text/html')
    
#     def post(self, request):
#         serializer = RegisterSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "회원가입 성공!"}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# from django.shortcuts import render
# from django.http import JsonResponse
# from django.views import View
# from .serializers import RegisterSerializer

# class RegisterView(View):

#     def get(self, request):
#         return render(request, 'register.html')
    
#     def post(self, request):
#         serializer = RegisterSerializer(data=request.POST)
#         if serializer.is_valid():
#             serializer.save()
#             return JsonResponse({"message": "회원가입 성공!"})
#         return JsonResponse(serializer.errors, status=400)


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