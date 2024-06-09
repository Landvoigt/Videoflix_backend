from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

class UserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')
        self.create_user_url = reverse('registry')
        self.reset_user_pw_url = reverse('password_reset_confirm', args=['uidb64', 'token'])

        self.user_data = {
            'username': 'username',
            'password': 'securepassword',
            'email': 'firstnamelastname@example.com',
        }

    def test_user_registration_and_login(self):
        response = self.client.post(self.create_user_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        login_data = {
            'email': 'firstnamelastname@example.com',
            'password': 'securepassword',
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)