from django.urls import path
from .views import FetchAndStoreProfilePictureView, VerifySnapshotView , UpdateProfilePictureView

urlpatterns = [
    path('fetch-and-store-profile-picture/', FetchAndStoreProfilePictureView.as_view(), name='fetch_and_store_profile_picture'),
    path('verify-snapshot/', VerifySnapshotView.as_view(), name='verify-snapshot'),
    path('update-test-profile-picture/', UpdateProfilePictureView.as_view(), name='update-test-profile-picture'),
]
