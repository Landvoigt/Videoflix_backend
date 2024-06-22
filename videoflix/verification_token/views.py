from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from rest_framework.views import APIView

from .models import EmailVerificationToken


class UserVerifyEmailView(APIView):
    def get(self, request, token, format=None):
        try:
            verification_token = EmailVerificationToken.objects.get(key=token)
            user = verification_token.user
            user.is_active = True
            user.save()
            verification_token.delete()
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/login?verified=true")
        except EmailVerificationToken.DoesNotExist:
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/error")