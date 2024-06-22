from django.conf import settings
from django.shortcuts import get_object_or_404, redirect

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import EmailVerificationToken


class UserVerifyEmailView(APIView):
    def get(self, request, token, format=None):
        try:
            verification_token = get_object_or_404(EmailVerificationToken, key=token)
            user = verification_token.user
            user.is_active = True
            user.save()
            verification_token.delete()
            return redirect(settings.FRONTEND_URL + '/login')
        except EmailVerificationToken.DoesNotExist:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)