from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.template.loader import render_to_string

from verification_token.models import EmailVerificationToken


def send_verification_email(user):
    try:
        verification_token = EmailVerificationToken.objects.get(user=user)
    except EmailVerificationToken.DoesNotExist:
        verification_token = EmailVerificationToken.objects.create(user=user)

    verification_url = settings.BACKEND_URL + reverse('verify_email', kwargs={'token': str(verification_token.key)})

    email_subject = 'Email Verification'
    email_body = render_to_string('verify_email.html', {
        'user': user,
        'verification_url': verification_url,
    })

    send_mail(
        email_subject,
        email_body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )