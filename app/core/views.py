import logging

import cv2
import face_recognition
import numpy as np
import os
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from PIL import Image

from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.authentication import CustomJWTAuthentication, TokenPayloadPermission
from .models import Profile

logger = logging.getLogger(__name__)


def _freelancer_id(request):
    """Return the candidate UUID from the verified JWT payload."""
    return request.auth.get('user_id') if request.auth else None


class FetchAndStoreProfilePictureView(APIView):
    """Upload and store a freelancer's reference profile picture."""
    permission_classes = [TokenPayloadPermission]
    authentication_classes = [CustomJWTAuthentication]

    def post(self, request, *args, **kwargs):
        freelancer_id = _freelancer_id(request)
        profile_picture = request.FILES.get('profile_picture')

        if not freelancer_id or not profile_picture:
            return Response(
                {"error": "Authentication and profile picture are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            freelancer = Profile.objects.filter(user_id=freelancer_id).first()
            if not freelancer:
                freelancer = Profile.objects.create(user_id=freelancer_id)

            if freelancer.profile_picture and freelancer.profile_picture.name == profile_picture.name:
                return Response({"message": "Profile picture is already up-to-date."}, status=status.HTTP_200_OK)

            freelancer.profile_picture.save(profile_picture.name, ContentFile(profile_picture.read()))
            freelancer.save()

            return Response(
                {"success": f"Successfully updated profile picture for freelancer {freelancer_id}."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception("Failed to update profile picture for %s", freelancer_id)
            return Response(
                {"error": f"Failed to update profile picture. Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifySnapshotView(APIView):
    permission_classes = [TokenPayloadPermission]
    authentication_classes = [CustomJWTAuthentication]

    def post(self, request, *args, **kwargs):
        freelancer_id = _freelancer_id(request)
        snapshot = request.FILES.get('screenshot')

        if not freelancer_id or not snapshot:
            return Response(
                {"error": "Authentication and snapshot image are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            snapshot_image = Image.open(snapshot)
            snapshot_image_array = np.array(snapshot_image)

            profile_face_encodings = cache.get(f"profile_face_encodings_{freelancer_id}")

            if not profile_face_encodings:
                try:
                    freelancer_profile = Profile.objects.get(user_id=freelancer_id)
                    profile_picture_path = freelancer_profile.profile_picture.path
                except Profile.DoesNotExist:
                    return Response(
                        {"error": "Freelancer profile not found."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                with ThreadPoolExecutor() as executor:
                    profile_future = executor.submit(face_recognition.load_image_file, profile_picture_path)
                    profile_image = profile_future.result()

                small_profile_image = cv2.resize(profile_image, (0, 0), fx=0.25, fy=0.25)
                profile_face_encodings = face_recognition.face_encodings(small_profile_image)

                if not profile_face_encodings:
                    return Response(
                        {"error": "Profile picture does not contain a detectable face.", "action": "pause"},
                        status=status.HTTP_200_OK,
                    )

                cache.set(f"profile_face_encodings_{freelancer_id}", profile_face_encodings)

            small_snapshot_image = cv2.resize(snapshot_image_array, (0, 0), fx=0.25, fy=0.25)
            snapshot_face_encodings = face_recognition.face_encodings(small_snapshot_image)

            if not snapshot_face_encodings:
                return Response(
                    {"error": "Snapshot does not contain a detectable face.", "action": "pause"},
                    status=status.HTTP_200_OK,
                )
            elif len(snapshot_face_encodings) > 1:
                return Response(
                    {"error": "Multiple faces detected in the snapshot. Only one face is allowed.", "action": "terminate"},
                    status=status.HTTP_200_OK,
                )

            match_results = face_recognition.compare_faces(
                profile_face_encodings, snapshot_face_encodings[0], tolerance=0.5
            )

            if any(match_results):
                return Response({"success": "Snapshot verified successfully.", "action": "continue"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Snapshot verification failed.", "action": "pause"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Snapshot verification error for %s", freelancer_id)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateProfilePictureView(APIView):
    """Update a freelancer's profile picture (must be the owner)."""
    permission_classes = [TokenPayloadPermission]
    authentication_classes = [CustomJWTAuthentication]

    def patch(self, request, *args, **kwargs):
        freelancer_id = _freelancer_id(request)
        profile_picture = request.FILES.get("profile_picture")

        if not freelancer_id or not profile_picture:
            return Response(
                {"error": "Authentication and profile picture are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            profile = Profile.objects.filter(user_id=freelancer_id).first()
            if not profile:
                return Response(
                    {"error": "Profile not found for the given freelancer ID."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            profile.profile_picture.save(profile_picture.name, ContentFile(profile_picture.read()))
            profile.save()

            return Response({"success": "Profile picture updated successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Failed to update profile picture for %s", freelancer_id)
            return Response(
                {"error": f"Failed to update profile picture. Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
