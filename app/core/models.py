# app/models.py
from django.db import models
import uuid
class FreelancerProfile(models.Model):
    freelancer_id = models.UUIDField(unique=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/')

class Profile(models.Model):
    user_id = models.UUIDField(unique=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/')