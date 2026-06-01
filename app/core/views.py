from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.authentication import CustomJWTAuthentication, TokenPayloadPermission
from django.core.files.base import ContentFile
import face_recognition
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.models import Profile
import os
from django.core.files.storage import default_storage
from django.conf import settings
import cv2
from io import BytesIO
from PIL import Image
import os
import face_recognition
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from django.core.cache import cache
from rest_framework import status
from .models import Profile

class FetchAndStoreProfilePictureView(APIView):
    """
    API View to upload and store a freelancer's profile picture efficiently.
    """
    permission_classes = [TokenPayloadPermission]
    authentication_classes = [CustomJWTAuthentication]

    def post(self, request, *args, **kwargs):
        freelancer_id = request.data.get('freelancer_id')
        profile_picture = request.FILES.get('profile_picture')

        # Validate input
        if not freelancer_id or not profile_picture:
            return Response(
                {"error": "Freelancer ID and profile picture are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Fetch the freelancer profile if it exists
            freelancer = Profile.objects.filter(user_id=freelancer_id).first()

            # If profile doesn't exist, create a new one
            if not freelancer:
                freelancer = Profile.objects.create(user_id=freelancer_id)

            # Check if the uploaded image is different from the existing one
            if freelancer.profile_picture and freelancer.profile_picture.name == profile_picture.name:
                return Response(
                    {"message": "Profile picture is already up-to-date."},
                    status=status.HTTP_200_OK
                )

            # Save the new profile picture
            freelancer.profile_picture.save(profile_picture.name, ContentFile(profile_picture.read()))
            freelancer.save()

            return Response(
                {"success": f"Successfully updated profile picture for freelancer {freelancer_id}."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to update profile picture. Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VerifySnapshotView(APIView):
    permission_classes = [TokenPayloadPermission]
    authentication_classes = [CustomJWTAuthentication]

    def post(self, request, *args, **kwargs):
        freelancer_id = request.data.get('freelancer_id')
        snapshot = request.FILES.get('screenshot')

        if not freelancer_id or not snapshot:
            return Response(
                {"error": "Freelancer ID and snapshot image are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            snapshot_image = Image.open(snapshot)
            snapshot_image_array = np.array(snapshot_image)

            # Check cache for profile face encodings
            profile_face_encodings = cache.get(f"profile_face_encodings_{freelancer_id}")

            if not profile_face_encodings:
                try:
                    freelancer_profile = Profile.objects.get(user_id=freelancer_id)
                    profile_picture_path = freelancer_profile.profile_picture.path
                except Profile.DoesNotExist:
                    return Response(
                        {"error": "Freelancer profile not found."},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Load and resize profile picture in parallel
                with ThreadPoolExecutor() as executor:
                    profile_future = executor.submit(face_recognition.load_image_file, profile_picture_path)
                    profile_image = profile_future.result()

                # Resize profile image for better performance
                small_profile_image = cv2.resize(profile_image, (0, 0), fx=0.25, fy=0.25)
                profile_face_encodings = face_recognition.face_encodings(small_profile_image)

                if not profile_face_encodings:
                    print("Profile picture does not contain a detectable face.")
                    return Response(
                        {"error": "Profile picture does not contain a detectable face.",
                         "action": "pause"},
                        status=status.HTTP_200_OK
                    )

                # Cache the profile face encodings
                cache.set(f"profile_face_encodings_{freelancer_id}", profile_face_encodings)

            # Resize snapshot image for face encoding
            small_snapshot_image = cv2.resize(snapshot_image_array, (0, 0), fx=0.25, fy=0.25)
            snapshot_face_encodings = face_recognition.face_encodings(small_snapshot_image)

            if not snapshot_face_encodings:
                print("Snapshot does not contain a detectable face.")
                return Response(
                    {"error": "Snapshot does not contain a detectable face.",
                     "action": "pause"},
                    status=status.HTTP_200_OK
                )
            elif len(snapshot_face_encodings) > 1:
                print("Multiple faces detected in the snapshot.")
                return Response(
                    {"error": "Multiple faces detected in the snapshot. Only one face is allowed.",
                     "action": "terminate"},
                    status=status.HTTP_200_OK
                )

            # Compare faces with a stricter tolerance
            match_results = face_recognition.compare_faces(profile_face_encodings, snapshot_face_encodings[0], tolerance=0.5)

            if any(match_results):
                print("Snapshot verified successfully.")
                return Response(
                    {"success": "Snapshot verified successfully." ,
                      "action": "continue"},
                    
                    status=status.HTTP_200_OK
                )
            else:
                print("Snapshot verification failed.")
                return Response(
                    {"error": "Snapshot verification failed.",
                     "action": "pause"},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateProfilePictureView(APIView):
    """
    API View to update a freelancer's profile picture.
    """
    permission_classes = [TokenPayloadPermission]
    authentication_classes = [CustomJWTAuthentication]

    def patch(self, request, *args, **kwargs):
        freelancer_id = request.data.get("freelancer_id")
        profile_picture = request.FILES.get("profile_picture")

        if not freelancer_id or not profile_picture:
            return Response(
                {"error": "Freelancer ID and profile picture are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if Profile exists
            profile = Profile.objects.filter(user_id=freelancer_id).first()
            if not profile:
                return Response(
                    {"error": "Profile not found for the given freelancer ID."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Update profile picture
            profile.profile_picture.save(profile_picture.name, ContentFile(profile_picture.read()))
            profile.save()

            return Response(
                {"success": "Profile picture updated successfully."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to update profile picture. Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )