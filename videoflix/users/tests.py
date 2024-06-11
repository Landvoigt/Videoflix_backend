from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

class UserCreateViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('register')

    def test_create_user_success(self):
        data = {
            'email': 'test@example.com',
            'password': 'strong_password_123'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('success', response.data)
        self.assertIn('username', response.data)
        self.assertTrue(User.objects.filter(email=data['email']).exists())

    def test_create_user_missing_email(self):
        data = {
            'password': 'strong_password_123'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Email and password are required.')

    def test_create_user_missing_password(self):
        data = {
            'email': 'test@example.com'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Email and password are required.')

    def test_create_user_already_exists(self):
        User.objects.create_user(username='existing_user', email='test@example.com', password='password')
        data = {
            'email': 'test@example.com',
            'password': 'strong_password_123'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'User already exists.')

    def test_create_user_server_error(self):
        original_create_user = User.objects.create_user
        User.objects.create_user = lambda *args, **kwargs: (_ for _ in ()).throw(Exception('Simulated error'))

        data = {
            'email': 'test@example.com',
            'password': 'strong_password_123'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertTrue(response.data['error'].startswith('Error creating user:'))

        User.objects.create_user = original_create_user


class UserLoginViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('login')
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='strong_password_123')

    def test_login_success_with_email(self):
        data = {
            'identifier': 'test@example.com',
            'password': 'strong_password_123'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user_id'], self.user.pk)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['username'], self.user.username)

    def test_login_success_with_username(self):
        data = {
            'identifier': 'testuser',
            'password': 'strong_password_123'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user_id'], self.user.pk)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['username'], self.user.username)

    def test_login_missing_identifier(self):
        data = {
            'password': 'strong_password_123'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Please provide email or username and password.')

    def test_login_missing_password(self):
        data = {
            'identifier': 'test@example.com'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Please provide email or username and password.')

    def test_login_invalid_email(self):
        data = {
            'identifier': 'nonexistent@example.com',
            'password': 'strong_password_123'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid email.')

    def test_login_invalid_username(self):
        data = {
            'identifier': 'nonexistentuser',
            'password': 'strong_password_123'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid username.')

    def test_login_invalid_password(self):
        data = {
            'identifier': 'test@example.com',
            'password': 'wrong_password'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid password.')


class UserUpdateUsernameTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='strong_password_123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.url = reverse('update_username')

    def test_update_username_success(self):
        data = {
            'new_username': 'new_testuser'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'new_testuser')

    def test_update_username_missing(self):
        data = {}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'New username is required.')

    def test_update_username_already_taken(self):
        User.objects.create_user(username='existinguser', email='existing@example.com', password='password')
        data = {
            'new_username': 'existinguser'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Username already taken.')

    def test_update_username_unauthenticated(self):
        self.client.credentials()
        data = {
            'new_username': 'new_testuser'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserPasswordResetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')

    def test_password_reset_token_created_and_email_sent(self):
        self.client.post(reverse('password_reset:reset-password-request'), {'email': self.user.email})

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password Reset', mail.outbox[0].subject)

        email_body = mail.outbox[0].body
        self.assertIn(self.user.username, email_body)

        token_line = [line for line in email_body.splitlines() if 'token' in line]
        self.assertTrue(token_line)
        
        token = token_line[0].split('token=')[1]
        self.assertTrue(token)

    def test_password_reset_with_token(self):
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        reset_confirm_url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        response = self.client.post(reset_confirm_url, {
            'password': 'newpassword123'
        }, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Password reset successfully.')

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_password_reset_with_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        reset_confirm_url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': 'invalid-token'})
        response = self.client.post(reset_confirm_url, {
            'password': 'newpassword123'
        }, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)