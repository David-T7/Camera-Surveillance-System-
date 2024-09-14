from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from core.models import FreelancerProfile
from django.core.files.uploadedfile import SimpleUploadedFile
import jwt
from django.conf import settings
import os

class VerifySnapshotViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.freelancer_id = '0c91fd82-97b1-42ed-a1ef-6fd7e60e3f57'
        self.url = reverse('verify-snapshot')

        # Path to real images
        self.test_images_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures')
        
        # Create a freelancer profile with a profile picture
        self.profile_picture = SimpleUploadedFile(
            name='profile_picture.png',
            content=open(os.path.join(self.test_images_path, 'profile_picture.png'), 'rb').read(),
            content_type='image/png'
        )
        self.freelancer_profile = FreelancerProfile.objects.create(
            freelancer_id=self.freelancer_id,
            profile_picture=self.profile_picture
        )

        # JWT token setup
        self.token = jwt.encode({'freelancer_id': self.freelancer_id}, settings.SECRET_KEY, algorithm='HS256')

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_verify_snapshot_success(self):
        """Test successfully verifying a snapshot."""
        snapshot = SimpleUploadedFile(
            name='valid_snapshot.png',
            content=open(os.path.join(self.test_images_path, 'valid_snapshot.png'), 'rb').read(),
            content_type='image/png'
        )

        data = {
            'freelancer_id': self.freelancer_id,
            'snapshot': snapshot,
        }

        self.authenticate()
        response = self.client.post(self.url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)

    def test_verify_snapshot_multiple_faces(self):
        """Test snapshot with multiple faces."""
        snapshot = SimpleUploadedFile(
            name='multiple_faces.png',
            content=open(os.path.join(self.test_images_path, 'multiple_faces.png'), 'rb').read(),
            content_type='image/png'
        )

        data = {
            'freelancer_id': self.freelancer_id,
            'snapshot': snapshot,
        }

        self.authenticate()
        response = self.client.post(self.url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_verify_snapshot_no_face(self):
        """Test snapshot where no face is detected."""
        snapshot = SimpleUploadedFile(
            name='no_face_image.png',
            content=open(os.path.join(self.test_images_path, 'no_face_image.png'), 'rb').read(),
            content_type='image/png'
        )

        data = {
            'freelancer_id': self.freelancer_id,
            'snapshot': snapshot,
        }

        self.authenticate()
        response = self.client.post(self.url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_verify_snapshot_mismatch(self):
        """Test snapshot that does not match the profile picture."""
        snapshot = SimpleUploadedFile(
            name='different_face.png',
            content=open(os.path.join(self.test_images_path, 'different_face.png'), 'rb').read(),
            content_type='image/png'
        )

        data = {
            'freelancer_id': self.freelancer_id,
            'snapshot': snapshot,
        }

        self.authenticate()
        response = self.client.post(self.url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
