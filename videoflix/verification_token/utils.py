from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from verification_token.models import EmailVerificationToken


# def send_verification_email(user):
#     # try:
#     #     verification_token = EmailVerificationToken.objects.get(user=user)
#     # except EmailVerificationToken.DoesNotExist:
#     #     verification_token = EmailVerificationToken.objects.create(user=user)
    
#     try:
#         verification_token = EmailVerificationToken.objects.get(user=user)
#         print(f"Existing token found: {verification_token.key}")
#     except EmailVerificationToken.DoesNotExist:
#         verification_token = EmailVerificationToken.objects.create(user=user)
#         print(f"New token created: {verification_token.key}")
#     except Exception as e:
#         print(f"Error generating token: {str(e)}")
#         raise

#     verification_url = settings.BACKEND_URL + reverse('verify_email', kwargs={'token': str(verification_token.key)})

#     subject = 'Videoflix Email Verification'
#     message = (
#         f"Hi {user.username}\n\n"
#         f"Please click the link below to verify your email address:\n"
#         f"<a href='{verification_url}'>Verify Email</a>\n\n"
#         "This email was sent from the Videoflix registration form.\n"
#         "If you did not create an account, no further action is required."
#     )

#     send_mail(
#         subject,
#         message,
#         settings.DEFAULT_FROM_EMAIL,
#         [user.email],
#         fail_silently=False,
#     )
    
    
from django.core.mail import send_mail
from django.utils.html import strip_tags

def send_verification_email(user):
    try:
        verification_token = EmailVerificationToken.objects.get(user=user)
        print(f"Existing token found: {verification_token.key}")
    except EmailVerificationToken.DoesNotExist:
        verification_token = EmailVerificationToken.objects.create(user=user)
        print(f"New token created: {verification_token.key}")
    except Exception as e:
        print(f"Error generating token: {str(e)}")
        raise

    verification_url = settings.BACKEND_URL + reverse('verify_email', kwargs={'token': str(verification_token.key)})

    subject = 'Videoflix Email Verification'
    
    html_message = (
        f"Hi {user.username},<br><br>"
        f"Please click the link below to verify your email address:<br>"
        f"<a href='{verification_url}'>Verify Email</a><br><br>"
        "This email was sent from the Videoflix registration form.<br>"
        "If you did not create an account, no further action is required."
    )

    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=html_message 
    )
