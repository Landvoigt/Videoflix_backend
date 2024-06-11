import traceback

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseNotFound
from django.dispatch import receiver
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

from django_rest_passwordreset.signals import reset_password_token_created
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken, Token, Response, APIView
from rest_framework.decorators import api_view, permission_classes

from .utils import generate_unique_username


class UserCreateView(APIView):
    def post(self, request, format=None):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if not User.objects.filter(email=email).exists():
                username = generate_unique_username()
                user = User.objects.create_user(username=username, email=email, password=password)
                return Response({'success': 'User created successfully.', 'username': username}, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'User already exists.'}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            traceback.print_exc()
            return Response({'error': f'Error creating user: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
        

class UserLoginView(ObtainAuthToken, APIView):
    def post(self, request, *args, **kwargs):
        identifier = request.data.get('identifier')
        password = request.data.get('password')

        if not identifier or not password:
            return Response({'error': 'Please provide email or username and password.'}, status=status.HTTP_400_BAD_REQUEST)

        if '@' in identifier:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                return Response({'error': 'Invalid email.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                return Response({'error': 'Invalid username.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({'error': 'Invalid password.'}, status=status.HTTP_401_UNAUTHORIZED)

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username': user.username,
        }, status=status.HTTP_200_OK)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_update_username(request):
    new_username = request.data.get('new_username')

    if not new_username:
        return Response({'error': 'New username is required.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=new_username).exists():
        return Response({'error': 'Username already taken.'}, status=status.HTTP_409_CONFLICT)

    request.user.username = new_username
    request.user.save()
    return Response({'success': 'Username updated successfully.'}, status=status.HTTP_200_OK)


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    if isinstance(reset_password_token, str):
        return
    user = reset_password_token.user
    subject = 'Password Reset'
    token = reset_password_token.key
    message = render_to_string('reset_password_email.html', {
        'user': user,
        'token': token,
    })
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


class UserResetPasswordView(APIView):
    # old but was working
    # def post(self, request):
    #     token = request.data.get('token')
    #     new_password = request.data.get('password')

    #     if not token or not new_password:
    #         return Response({'error': 'Token and new_password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
    #     user = get_object_or_404(User, password_reset_token=token)
    #     user.set_password(new_password)
    #     user.save()

    #     return Response({'message': 'Password reset successfully.'})
    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            new_password = request.data.get('password')
            if not new_password:
                return Response({'error': 'Password is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password reset successfully.'})
        else:
            return Response({'error': 'Invalid token or user ID.'}, status=status.HTTP_400_BAD_REQUEST)