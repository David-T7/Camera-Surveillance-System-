from django.urls import path
from .views import FetchAndStoreProfilePictureView, VerifySnapshotView

urlpatterns = [
    path('fetch-and-store-profile-picture/', FetchAndStoreProfilePictureView.as_view(), name='fetch_and_store_profile_picture'),
    path('verify-snapshot/', VerifySnapshotView.as_view(), name='verify-snapshot'),
]
