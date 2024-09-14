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

class FetchAndStoreProfilePictureView(APIView):
    """
    API View to upload and store a freelancer's profile picture.
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
        # Fetch or create the freelancer profile
        try:
            freelancer, created = Profile.objects.get_or_create(user_id=freelancer_id)
            print("freelancer is ",freelancer)
            # Store the profile picture
            if(created):
                freelancer.profile_picture.save(profile_picture.name, ContentFile(profile_picture.read()))

            return Response(
                {"success": f"Successfully stored profile picture for freelancer {freelancer_id}."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to store profile picture for freelancer {freelancer_id}. Error: {str(e)}"},
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

        media_root = settings.MEDIA_ROOT
        file_extension = os.path.splitext(snapshot.name)[1] or '.jpg'  # Default to .jpg if no extension
        snapshot_path = os.path.join(media_root, 'screen_shot', f'snapshot{file_extension}')
        profile_picture_path = None

        try:
            print(f"Saving snapshot to: {snapshot_path}")
            # Save the snapshot file with extension
            with default_storage.open(snapshot_path, 'wb+') as destination:
                for chunk in snapshot.chunks():
                    destination.write(chunk)

            # Verify file existence
            if not os.path.exists(snapshot_path):
                print(f"Snapshot file does not exist at: {snapshot_path}")
                return Response(
                    {"error": "Snapshot file does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Load and process profile picture
            try:
                freelancer_profile = Profile.objects.get(user_id=freelancer_id)
                profile_picture_path = freelancer_profile.profile_picture.path
                print(f"Profile picture path: {profile_picture_path}")

                profile_image = face_recognition.load_image_file(profile_picture_path)
                profile_face_encodings = face_recognition.face_encodings(profile_image)
                
                if not profile_face_encodings:
                    print("Profile picture does not contain a detectable face.")
                    return Response(
                        {"error": "Profile picture does not contain a detectable face.",
                         "action": "pause"},
                        status=status.HTTP_200_OK
                    )

            except Profile.DoesNotExist:
                print("Freelancer profile not found.")
                return Response(
                    {"error": "Freelancer profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Load and process snapshot
            snapshot_image = face_recognition.load_image_file(snapshot_path)
            snapshot_face_encodings = face_recognition.face_encodings(snapshot_image)

            if not snapshot_face_encodings:
                print("Snapshot does not contain a detectable face.")
                return Response(
                    {"error": "Snapshot does not contain a detectable face.",
                     "action": "pause"},
                    status=status.HTTP_200_OK
                )

            # Compare faces
            match_results = face_recognition.compare_faces(profile_face_encodings, snapshot_face_encodings[0])

            if any(match_results):
                print("Snapshot verified successfully.")
                response = Response(
                    {"success": "Snapshot verified successfully."},
                    status=status.HTTP_200_OK
                )
            else:
                print("Snapshot verification failed.")
                response = Response(
                    {"error": "Snapshot verification failed.",
                     "action": "pause"},
                    status=status.HTTP_200_OK
                )

        finally:
            # Clean up temporary snapshot file
            if os.path.exists(snapshot_path):
                os.remove(snapshot_path)

        return response
