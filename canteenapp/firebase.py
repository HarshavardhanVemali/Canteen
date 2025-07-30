# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import UserDeviceToken
from firebase_admin import messaging
import firebase_admin
from firebase_admin import credentials
import json

# Initialize Firebase if not already done
cred_path = "/Users/harsha/Projects/canteen/foodhub-c60e4-firebase-adminsdk-oxz22-3e6b763fd3.json"  # Use your actual credentials file path
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

@csrf_exempt  # To bypass CSRF token for API calls
def send_notification(request):
    """
    Sends a push notification to a list of users based on the provided user IDs and message.
    """
    if request.method == "POST":
        try:
            # Get the data from the request
            data = json.loads(request.body)
            user_ids = data.get('user_ids', [])
            title = data.get('title', '')
            body = data.get('body', '')
            url = data.get('url', None)

            if not user_ids or not title or not body:
                return JsonResponse({"error": "Missing required fields"}, status=400)
            
            # Fetch the device registration tokens for the given user_ids
            registration_tokens = list(UserDeviceToken.objects.filter(user__email__in=user_ids).values_list('device_registration_token', flat=True))
            if not registration_tokens:
                return JsonResponse({"error": "No registration tokens found for provided user IDs"}, status=404)
            
            # Construct the message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={'url': url} if url else {},  # Send the URL if provided
                tokens=registration_tokens,
            )

            # Send the message
            response = messaging.send_multicast(message)
            
            return JsonResponse({
                'success_count': response.success_count,
                'failure_count': response.failure_count
            })
        
        except Exception as e:
            print(str(e))
            return JsonResponse({"error": str(e)}, status=500)
            

    return JsonResponse({"error": "Invalid request method"}, status=405)
