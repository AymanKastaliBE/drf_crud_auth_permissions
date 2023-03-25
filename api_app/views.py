from django.shortcuts import redirect
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import BookSerializer, UserSerializer
from django.contrib.auth.views import LogoutView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from .permissions import IsOwner
from django.contrib.auth.hashers import make_password

class Books(generics.ListCreateAPIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        for obj in queryset:
            print(obj.author)
        return queryset
    
    def perform_create(self, serializer):
        title = serializer.validated_data.get('title')
        published_date = serializer.validated_data.get('published_date')
        serializer.save(title=title, published_date=published_date, author=self.request.user.author)


class BookDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    
    
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        username = serializer.validated_data['username']
        password = make_password(serializer.validated_data['password'])
        # self.perform_create(serializer)
        user_data = {
            'username': username,
            'password': password,
        }
        serializer.save(**user_data)
        user = User.objects.get(username=username)
        author = Author.objects.create(user=user)
        token, created = Token.objects.get_or_create(user=user)
        context = {
            'token': token.key,
            'author': author.user.username
        }
        headers = self.get_success_headers(serializer.data)
        response = Response(context, status=status.HTTP_201_CREATED, headers=headers)
        # return response
        return redirect('login')

    
class LoginView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            # return Response({'token': token.key})
            return redirect('books')
        else:
            return Response({'error': 'Invalid username or password'})
        
        
class MyLogoutView(LogoutView):
    next_page = '/admin'