import requests
from django.core.files.base import ContentFile
from .models import FreelancerProfile

def fetch_and_store_profile_picture(freelancer_id, api_url, token):
    # Set up headers to include the authentication token
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
    }

    # Make the API request to fetch freelancer data
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        # Fetch freelancer data (assuming it's in JSON format)
        data = response.json()
        
        # Extract relevant fields
        profile_picture_url = data.get('profile_picture_url')
        name = data.get('name')
        email = data.get('email')
        
        # Fetch the profile picture
        image_response = requests.get(profile_picture_url, headers=headers)
        if image_response.status_code == 200:
            # Store the profile picture in the model
            freelancer, created = FreelancerProfile.objects.get_or_create(freelancer_id=freelancer_id)
            freelancer.profile_picture.save(
                f"freelancer_{freelancer_id}.jpg",
                ContentFile(image_response.content),
                save=True
            )
            return freelancer
        else:
            print(f"Failed to fetch image for freelancer {freelancer_id}")
    else:
        print(f"Failed to fetch data for freelancer {freelancer_id}")

    return None
