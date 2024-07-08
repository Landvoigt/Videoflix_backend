from datetime import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


@method_decorator(csrf_exempt, name='dispatch')
class ContactView(APIView):
    def post(self, request):
        first_name = request.data.get('firstName')
        last_name = request.data.get('lastName')
        company = request.data.get('company')
        email = request.data.get('email')
        message = request.data.get('message')
        current_date = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

        subject = "New Contact Submission from Videoflix"
        message = (
            f"New Contact Form Submission from Videoflix\n\n"
            f"Date: {current_date}\n"
            f"First Name: {first_name}\n"
            f"Last Name: {last_name}\n"
            f"Company: {company}\n"
            f"Email: {email}\n"
            f"Message:\n{message}\n\n"
            "This email was sent from the Videoflix contact form."
        )

        recipient_list = [settings.CONTACT_EMAIL_1, settings.CONTACT_EMAIL_2]

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                fail_silently=False,
            )
            return Response({"message": "Email sent successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)