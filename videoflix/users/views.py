import traceback

from django.conf import settings
from django.dispatch import receiver
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken, Token, Response, APIView
from django_rest_passwordreset.signals import reset_password_token_created


class UserLoginView(ObtainAuthToken, APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Email does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({'error': 'Invalid password.'}, status=status.HTTP_401_UNAUTHORIZED)

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username': user.username,
        }, status=status.HTTP_200_OK)
    

class UserCreateView(APIView):
    def post(self, request, format=None):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(username=username, email=email, password=password)
                return Response({'success': 'User created successfully.'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'User already exists.'}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            traceback.print_exc()
            return Response({'error': f'Error creating user: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    if isinstance(reset_password_token, str):
        return
    user = reset_password_token.user
    subject = 'Password Reset'
    message = (
        f'Hello {user.username},\n\n'
        'You have requested to reset your password. Please click the following link to reset it:\n'
        f'https://joinnew.timvoigt.ch/html/resetPassword.html?token={reset_password_token.key}'
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


class UserResetPasswordView(APIView):
     def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('password')

        if not token or not new_password:
            return Response({'error': 'Token and new_password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(User, password_reset_token=token)
        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password reset successfully.'})