from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from core.models import FreelancerProfile
from django.core.files.uploadedfile import SimpleUploadedFile
import jwt
from django.conf import settings
import os

class FetchAndStoreProfilePictureViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.freelancer_id = '0c91fd82-97b1-42ed-a1ef-6fd7e60e3f57'
        self.url = reverse('fetch-profile-picture')

        # JWT token setup
        self.token = jwt.encode({'freelancer_id': self.freelancer_id}, settings.SECRET_KEY, algorithm='HS256')

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_store_profile_picture_success(self):
        """Test uploading and storing a profile picture successfully."""
        # Load the actual image file
        image_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures', 'bmw.png')
        with open(image_path, 'rb') as image_file:
            image = SimpleUploadedFile(
                name='bmw.png',
                content=image_file.read(),
                content_type='image/png'
            )

        data = {
            'freelancer_id': self.freelancer_id,
            'profile_picture': image,
        }

        self.authenticate()
        response = self.client.post(self.url, data, format='multipart')
        print("respose is ",response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)

        # Check that the freelancer profile was created and the picture was stored
        freelancer_profile = FreelancerProfile.objects.get(freelancer_id=self.freelancer_id)
        self.assertTrue(freelancer_profile.profile_picture)  # Check that the picture is stored

    def test_store_profile_picture_missing_file(self):
        """Test uploading without a profile picture file."""
        data = {
            'freelancer_id': self.freelancer_id,
            # 'profile_picture' is intentionally missing
        }

        self.authenticate()
        response = self.client.post(self.url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_store_profile_picture_invalid_token(self):
        """Test uploading a profile picture with an invalid token."""
        # Load the actual image file
        image_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures', 'bmw.png')
        with open(image_path, 'rb') as image_file:
            image = SimpleUploadedFile(
                name='bmw.png',
                content=image_file.read(),
                content_type='image/png'
            )

        data = {
            'freelancer_id': self.freelancer_id,
            'profile_picture': image,
        }

        # Set an invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken')
        response = self.client.post(self.url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)  # JWT returns 'detail' in case of authentication failure
