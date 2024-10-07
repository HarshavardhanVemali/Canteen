from django.shortcuts import render,redirect
from .models import FailedLoginAttempts
import uuid
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Permission, ContentType
from django.contrib.auth.decorators import user_passes_test
import smtplib
import dns.resolver
import socket
import json
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings  
from .models import EmailVerification
import random
import string
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

def admin_required(view_func):
    return user_passes_test(
        lambda u: u.is_superuser, 
        login_url='/adminlogin/'
    )(view_func)

def deliveryperson_required(view_func):
    return user_passes_test(
        lambda u: u.has_perm('canteenapp.is_deliveryperson') and not u.is_superuser,
        login_url='/deliverypersonlogin/'
    )(view_func)

def user_required(view_func):
    return user_passes_test(
        lambda u: u.is_active and (u.is_superuser or u.has_perm('canteenapp.is_user') or u.has_perm('canteenapp.is_deliveryperson')),
        login_url='/userlogin/'
    )(view_func)


def index(request):
    return render(request,'index.html')

@user_required
def home(request):
    return render(request,'home.html')

MAX_FAILED_ATTEMPTS = 3

def set_device_cookie(response, device_id):
    response.set_cookie('device_id', device_id, max_age=365 * 24 * 60 * 60)

def get_device_id(request):
    return request.COOKIES.get('device_id', str(uuid.uuid4()))

def is_device_blocked(device_id):
    try:
        failed_attempt = FailedLoginAttempts.objects.get(device_id=device_id)
        if failed_attempt.is_active:
            return True
    except FailedLoginAttempts.DoesNotExist:
        return False
    return False

def adminlogin(request):
    if request.method == 'POST':
        device_id = get_device_id(request)
        if is_device_blocked(device_id):
            return render(request, 'adminlogin.html', {'blocked': True,'error_message': 'Your device is permanently blocked due to multiple failed login attempts.'})

        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_superuser or (user.is_staff and not user.is_active):
                FailedLoginAttempts.objects.filter(device_id=device_id).update(attempts=0, is_active=False)
                response = redirect('admindashboard')
                set_device_cookie(response, device_id)
                login(request, user)
                return response
            else:
                return render(request, 'adminlogin.html', {'error_message': 'You do not have permission to access the admin page.'})
        else:
            failed_attempt, created = FailedLoginAttempts.objects.get_or_create(device_id=device_id)
            if not created:
                failed_attempt.attempts += 1
                failed_attempt.save()
                if failed_attempt.attempts >= MAX_FAILED_ATTEMPTS:
                    failed_attempt.is_active = True
                    failed_attempt.save()
                    return render(request, 'adminlogin.html', {'blocked': True, 'error_message': 'Your device is permanently blocked due to multiple failed login attempts.'})
            else:
                failed_attempt.attempts = 1
                failed_attempt.save()
            return render(request, 'adminlogin.html', {'error_message': 'Invalid username or password'})
    else:
        response = render(request, 'adminlogin.html')
        if 'device_id' not in request.COOKIES:
            device_id = get_device_id(request)
            set_device_cookie(response, device_id)
        return response

@admin_required
def admindashboard(request):
    return render(request,'admindashboard.html')


def verify_email_smtp(email):
    domain = email.split('@')[-1]
    smtp_servers = {
        'gmail.com': ('smtp.gmail.com', 587),
        'yahoo.com': ('smtp.mail.yahoo.com', 587),
        'outlook.com': ('smtp.office365.com', 587),
        'hotmail.com': ('smtp.office365.com', 587),
    }

    server, port = smtp_servers.get(domain, (None, None)) 

    if server is None:
        return False  

    try:
        with smtplib.SMTP(server, port) as server:
            server.starttls() 
            server.ehlo()  
            server.mail('your-email@your-domain.com') 
            code, _ = server.rcpt(email)
            return code == 250  
    except (smtplib.SMTPException, socket.error) as e:
        return False 

@csrf_exempt
def loginverifymail(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            entered_code = data.get('code')

            User = get_user_model()
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found.'})
            print(user)
            try:
                verification = EmailVerification.objects.get(email=email)

                if verification.is_expired():
                    return JsonResponse({'success': False, 'error': 'Verification code has expired.'})

                if verification.verification_code == entered_code:
                    verification.is_verified = True
                    verification.save()

                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)

                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Incorrect verification code.'})
            except EmailVerification.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'No verification request found for this email.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@csrf_exempt
def sendverificationcode(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email_login')
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found.'})

            
            verification_code = ''.join(random.choice(string.digits) for _ in range(6))
            expiration_time = timezone.now() + timezone.timedelta(minutes=10)

            try:
                verification, created = EmailVerification.objects.get_or_create(email=email)
                
                verification.verification_code = verification_code
                verification.created_at = timezone.now()  
                verification.expiration_time = timezone.now() + timezone.timedelta(minutes=10)
                verification.is_verified =  False
                verification.save()  

            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error while generating verification code: {str(e)}'})
            html_content = render_to_string("loginverification.html", context={
                'verification_code': verification_code,
                'user_name': user.username,
                'time': timezone.localtime(expiration_time)
            })
            text_content = strip_tags(html_content)
            subject = 'Verification Code'
            from_email = 'vemalivardhan@gmail.com'
            recipient_list = [email]
            email_message = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

def loginverification(request):
    return render(request, 'loginverification.html')
    
def signupverification(request):
    return render(request,'signupverification.html')

@csrf_exempt
def signupverifymail(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            entered_code = data.get('code')

            User = get_user_model()
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found.'})

            try:
                verification = EmailVerification.objects.get(email=email)

                if verification.is_expired():
                    return JsonResponse({'success': False, 'error': 'Verification code has expired.'})

                if verification.verification_code == entered_code:
                    verification.is_verified = True
                    verification.save()

                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)

                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Incorrect verification code.'})
            except EmailVerification.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'No verification request found for this email.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@csrf_exempt
def sendsignupverificationcode(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email_login')
            User = get_user_model()
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'User already exists.'})
            verification_code = ''.join(random.choice(string.digits) for _ in range(6))
            expiration_time = timezone.now() + timezone.timedelta(minutes=10)

            try:
                verification, created = EmailVerification.objects.get_or_create(email=email)
                verification.verification_code = verification_code
                verification.created_at = timezone.now()
                verification.expiration_time = expiration_time
                verification.is_verified = False
                verification.save()

            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error while generating verification code: {str(e)}'})

            html_content = render_to_string("signupverification.html", context={
                'verification_code': verification_code,
                'time': timezone.localtime(expiration_time)
            })
            text_content = strip_tags(html_content)
            subject = 'Verification Code'
            from_email = 'vemalivardhan@gmail.com'
            recipient_list = [email]
            email_message = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})