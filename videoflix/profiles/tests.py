from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APIClient
from rest_framework import status

from .models import Profile


class ProfileViewSetTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create some profiles for testing
        self.profile1 = Profile.objects.create(user=self.user, name="Profile 1", avatar_id=1)
        self.profile2 = Profile.objects.create(user=self.user, name="Profile 2", avatar_id=2)

    def test_list_profiles(self):
        url = '/profiles/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Assuming only 2 profiles exist for this user

    def test_retrieve_profile(self):
        url = f'/profiles/{self.profile1.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Profile 1')

    def test_create_profile(self):
        url = '/profiles/'
        data = {'name': 'Profile 3', 'avatar_id': 3}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 3)  # Check if profile count increased

    def test_update_profile(self):
        url = f'/profiles/{self.profile1.id}/'
        data = {'name': 'Updated Profile 1'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Profile 1')

    def test_delete_profile(self):
        url = f'/profiles/{self.profile1.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Profile.objects.filter(id=self.profile1.id).exists())

    def test_validation_error_missing_name(self):
        url = '/profiles/'
        data = {'avatar_id': 6}  # Missing 'name' field
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)  # Check if 'name' field error is present

    def test_validation_error_missing_avatar(self):
        url = '/profiles/'
        data = {'name': 'Profile 6'}  # Missing 'avatar_id' field
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('avatar_id', response.data)  # Check if 'avatar_id' field error is present