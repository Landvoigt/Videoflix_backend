from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from verification_token.models import EmailVerificationToken


def send_verification_email(user):
    try:
        verification_token = EmailVerificationToken.objects.get(user=user)
    except EmailVerificationToken.DoesNotExist:
        verification_token = EmailVerificationToken.objects.create(user=user)

    verification_url = settings.BACKEND_URL + reverse('verify_email', kwargs={'token': str(verification_token.key)})

    subject = 'Videoflix Email Verification'
    message = (
        f"Hi {user.username}\n\n"
        f"Please click the link below to verify your email address:\n"
        f"<a href='{verification_url}'>Verify Email</a>\n\n"
        "This email was sent from the Videoflix registration form.\n"
        "If you did not create an account, no further action is required."
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )