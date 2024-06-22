from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from .models import Profile


class ProfileViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        
        self.profile1 = Profile.objects.create(user=self.user, name="Profile 1", avatar_id=1)
        self.profile2 = Profile.objects.create(user=self.user, name="Profile 2", avatar_id=2)
        
    def tearDown(self):
        self.client.credentials()
        self.user.delete()
        Profile.objects.all().delete()
        
    def test_get_profiles(self):
        response = self.client.get('/profiles/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Profile 1')
        self.assertEqual(response.data[1]['name'], 'Profile 2')
        
    def test_create_profile(self):
        data = {
            "name": "Test Profile",
            "avatar_id": 3
        }
        response = self.client.post('/profiles/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Test Profile')
        self.assertEqual(response.data['avatar_id'], 3)
        self.assertEqual(Profile.objects.count(), 3)
        
    def test_update_profile(self):
        data = {
            "id": self.profile1.id,
            "name": "Updated Profile 1"
        }
        response = self.client.patch('/profiles/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.name, 'Updated Profile 1')
        
    def test_delete_profile(self):
        data = {
            "id": self.profile1.id
        }
        response = self.client.delete('/profiles/', data, format='json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Profile.objects.count(), 1)