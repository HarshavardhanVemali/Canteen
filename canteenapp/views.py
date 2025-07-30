from django.shortcuts import render,redirect
from .models import *
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
from django.views.decorators.csrf import csrf_exempt,csrf_protect
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
import os
from django.contrib.auth.hashers import make_password,check_password
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import logout
from django.db.models import Q
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.utils import timezone
from django.utils.timezone import timedelta
from django.db.models import F, Case, When
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
import requests
import json
import hashlib
import base64
import requests
import uuid
import logging
import datetime
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import HttpResponseBadRequest
from decimal import Decimal
from cryptography.hazmat.primitives import hashes
from django.views.decorators.csrf import csrf_exempt
from cryptography.hazmat.backends import default_backend
import jsons
import time
from .utils import generate_checksum
import payu_sdk
import hashlib
import uuid  
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient
from phonepe.sdk.pg.env import Env
import base64
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import UserDeviceToken
from django.contrib.auth import get_user_model
from .models import UserDeviceToken
from firebase_admin import messaging
import firebase_admin
from firebase_admin import credentials
import json
from django.shortcuts import get_object_or_404
from random import choice
import os
from django.db.models import Min

def admin_required(view_func):
    return user_passes_test(
        lambda u: u.is_superuser, 
        login_url='/adminlogin/'
    )(view_func)

def delivery_app_required(view_func):
    return user_passes_test(
        lambda u: u.has_perm('canteenapp.is_deliveryperson') and not u.is_superuser,
        login_url='/deliveryapplogin/'
    )(view_func)

def user_required(view_func):
    return user_passes_test(
        lambda u: u.is_active and (u.is_superuser or u.has_perm('canteenapp.is_user') ),
        login_url='/userlogin/'
    )(view_func)

def app_user_required(view_func):
    return user_passes_test(
        lambda u: u.is_active and (u.is_superuser or u.has_perm('canteenapp.is_user')) ,
        login_url='/applogin/'
    )(view_func)

def restaurant_required(view_func):
    return user_passes_test(
        lambda u: u.has_perm('canteenapp.is_restaurant') and not u.is_superuser,
        login_url='/resturantlogin/'
    )(view_func)

def restaurant_app_required(view_func):
    return user_passes_test(
        lambda u: u.has_perm('canteenapp.is_restaurant') and not u.is_superuser,
        login_url='/restaurantapplogin/'
    )(view_func)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    return render(request,'index.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_required
def home(request):
    return render(request,'home.html')
#admin

MAX_FAILED_ATTEMPTS = 3
channel_layer = get_channel_layer()

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
        print(user)
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
def admintemplate(request):
    return render(request,'admintemplate.html')

@admin_required
def admindashboard(request):
    return render(request,'admindashboard.html')

@require_http_methods(["GET"])
@admin_required
@csrf_protect
def admin_sales_overview(request):
    today = timezone.now().date()

    last_seven_days = [today - timedelta(days=x) for x in range(7)]

    last_five_weeks = [today - timedelta(weeks=x) for x in range(5)]


    last_twelve_months = [today - timedelta(days=30 * x) for x in range(12)]


    seven_days_orders_data = [
        Order.objects.filter(created_at__date=date).count() 
        for date in last_seven_days
    ]

    five_weeks_orders_data = [
        Order.objects.filter(created_at__date__range=[date - timedelta(days=6), date]).count() 
        for date in last_five_weeks
    ]

    twelve_months_orders_data = [
        Order.objects.filter(created_at__year=date.year, created_at__month=date.month).count()
        for date in last_twelve_months
    ]

   
    seven_days_revenue_data = [
        Order.objects.filter(created_at__date=date).aggregate(total_revenue=Sum('total_price'))['total_revenue'] or 0
        for date in last_seven_days
    ]

    five_weeks_revenue_data = [
        Order.objects.filter(created_at__date__range=[date - timedelta(days=6), date]).aggregate(total_revenue=Sum('total_price'))['total_revenue'] or 0
        for date in last_five_weeks
    ]
    twelve_months_revenue_data = [
        Order.objects.filter(created_at__year=date.year, created_at__month=date.month).aggregate(total_revenue=Sum('total_price'))['total_revenue'] or 0
        for date in last_twelve_months
    ]


    orders_chart_data = {
        'labels': [date.strftime('%Y-%m-%d') for date in last_seven_days],
        'datasets': [{
            'label': 'Orders (Past 7 Days)',
            'data': list(reversed(seven_days_orders_data)),
            'backgroundColor': 'rgba(247, 103, 0, 1)', 
            'borderColor': 'rgba(247, 103, 0, 1)',  
            'borderWidth': 1
        }]
    }

    orders_chart_data_week = {
        'labels': [date.strftime('%Y-%m-%d') for date in last_five_weeks],
        'datasets': [{
            'label': 'Orders (Past 5 Weeks)',
            'data': list(reversed(five_weeks_orders_data)),
            'backgroundColor': 'rgba(54, 162, 235, 1)',  
            'borderColor': 'rgba(54, 162, 235, 1)',  
            'borderWidth': 1
        }]
    }

    orders_chart_data_month = {
        'labels': [date.strftime('%Y-%m') for date in last_twelve_months],
        'datasets': [{
            'label': 'Orders (Past 12 Months)',
            'data': list(reversed(twelve_months_orders_data)),
            'backgroundColor': 'rgba(255, 206, 86, 1)', 
            'borderColor': 'rgba(255, 206, 86, 1)', 
            'borderWidth': 1
        }]
    }

    revenue_chart_data = {
        'labels': [date.strftime('%Y-%m-%d') for date in last_seven_days],
        'datasets': [{
            'label': 'Revenue (Past 7 Days)',
            'data': list(reversed(seven_days_revenue_data)),
            'backgroundColor': 'rgba(54, 162, 235, 1)', 
            'borderColor': 'rgba(54, 162, 235, 1)', 
            'borderWidth': 1
        }]
    }

    revenue_chart_data_week = {
        'labels': [date.strftime('%Y-%m-%d') for date in last_five_weeks],
        'datasets': [{
            'label': 'Revenue (Past 5 Weeks)',
            'data': list(reversed(five_weeks_revenue_data)),
            'backgroundColor': 'rgba(0, 91, 247, 1)',  
            'borderColor': 'rgba(0, 91, 247, 1)', 
            'borderWidth': 1
        }]
    }

    revenue_chart_data_month = {
        'labels': [date.strftime('%Y-%m') for date in last_twelve_months],
        'datasets': [{
            'label': 'Revenue (Past 12 Months)',
            'data': list(reversed(twelve_months_revenue_data)),
            'backgroundColor': 'rgba(75, 192, 192, 1)', 
            'borderColor': 'rgba(75, 192, 192, 1)',  
            'borderWidth': 1
        }]
    }

    context = {
        'orders_chart_data': orders_chart_data,
        'orders_chart_data_week': orders_chart_data_week,
        'orders_chart_data_month': orders_chart_data_month,
        'revenue_chart_data': revenue_chart_data,
        'revenue_chart_data_week': revenue_chart_data_week,
        'revenue_chart_data_month': revenue_chart_data_month,
    }
    return JsonResponse({'success': True, 'context': context})

@require_http_methods(["GET"])
@admin_required
@csrf_protect
def admingettopsellingitems(request):
    if request.method == 'GET':
        top_selling_items = (
            OrderItem.objects
            .values('item__item_name', 'item__item_image')  
            .annotate(total_quantity=Sum('quantity'), total_revenue=Sum('total_price'))
            .order_by('-total_quantity')[:10]
        )
        data = []
        for item in top_selling_items:
            image_url = (
                f"{settings.MEDIA_URL}{item['item__item_image']}" 
                if item['item__item_image'] 
                else None
            )
            data.append({
                'item_name': item['item__item_name'],
                'item_image': image_url,
                'total_quantity': item['total_quantity'],
                'total_revenue': item['total_revenue'],
            })

        return JsonResponse({'success': True, 'data': data})
    return JsonResponse({'success':False,'error':'Invalid request method'})
    
@require_http_methods(["GET"])
@admin_required
@csrf_protect
def admin_order_breakdown(request):
    today = timezone.now().date()
    last_week_start = today - timedelta(days=7)
    last_five_weeks_start = today - timedelta(weeks=5)
    last_year_start = today - timedelta(days=365)

    seven_days_breakdown = (
        Order.objects
        .filter(created_at__gte=last_week_start, created_at__lte=today)
        .values('delivery_type')
        .annotate(order_count=Count('id'), unique_users=Count('user', distinct=True)) 
    )

    five_weeks_breakdown = (
        Order.objects
        .filter(created_at__gte=last_five_weeks_start, created_at__lte=today)
        .values('delivery_type')
        .annotate(order_count=Count('id'), unique_users=Count('user', distinct=True))
    )

    twelve_months_breakdown = (
        Order.objects
        .filter(created_at__gte=last_year_start, created_at__lte=today)
        .values('delivery_type')
        .annotate(order_count=Count('id'), unique_users=Count('user', distinct=True))
    )


    seven_days_breakdown = list(seven_days_breakdown)
    five_weeks_breakdown = list(five_weeks_breakdown)
    twelve_months_breakdown = list(twelve_months_breakdown)


    order_breakdown_chart_data = {
        'labels': [item['delivery_type'] for item in seven_days_breakdown],
        'datasets': [{
            'label': 'Order Count (Past 7 Days)',
            'data': [item['order_count'] for item in seven_days_breakdown],
            'backgroundColor': [
                'rgba(247, 103, 0, 1)', 
                'rgba(54, 162, 235, 1)', 
                'rgba(75, 192, 192, 1)'  
            ],
            'borderColor': [
                'rgba(247, 103, 0, 1)',  
                'rgba(54, 162, 235, 1)',  
                'rgba(75, 192, 192, 1)' 
            ],
            'borderWidth': 1
        }]
    }

    order_breakdown_chart_data_week = {
        'labels': [item['delivery_type'] for item in five_weeks_breakdown],
        'datasets': [{
            'label': 'Order Count (Past 5 Weeks)',
            'data': [item['order_count'] for item in five_weeks_breakdown],
            'backgroundColor': [
                'rgba(247, 103, 0, 1)',  
                'rgba(54, 162, 235, 1)', 
                'rgba(75, 192, 192, 1)'   
            ],
            'borderColor': [
                'rgba(247, 103, 0, 1)',  
                'rgba(54, 162, 235, 1)', 
                'rgba(75, 192, 192, 1)'  
            ],
            'borderWidth': 1
        }]
    }

    order_breakdown_chart_data_month = {
        'labels': [item['delivery_type'] for item in twelve_months_breakdown],
        'datasets': [{
            'label': 'Order Count (Past 12 Months)',
            'data': [item['order_count'] for item in twelve_months_breakdown],
            'backgroundColor': [
                'rgba(247, 103, 0, 1)',  
                'rgba(54, 162, 235, 1)',  
                'rgba(75, 192, 192, 1)'   
            ],
            'borderColor': [
                'rgba(247, 103, 0, 1)', 
                'rgba(54, 162, 235, 1)',  
                'rgba(75, 192, 192, 1)'  
            ],
            'borderWidth': 1
        }]
    }

    context = {
        'order_breakdown_chart_data': order_breakdown_chart_data,
        'order_breakdown_chart_data_week': order_breakdown_chart_data_week,
        'order_breakdown_chart_data_month': order_breakdown_chart_data_month,
        'seven_days_breakdown': seven_days_breakdown,  
        'five_weeks_breakdown': five_weeks_breakdown,  
        'twelve_months_breakdown': twelve_months_breakdown,  
    }
    return JsonResponse({'success': True, 'context': context})

@require_http_methods(["GET"])
@admin_required
@csrf_protect
def admin_order_counts(request):
    all_orders = Order.objects.all().count()
    new_orders = Order.objects.filter(status='pending').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()

    context = {
        'all_orders': all_orders,
        'new_orders': new_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
    }
    return JsonResponse({'success': True, 'context': context})


@admin_required
def admindeliverypersonal(request):
    return render(request,'admindeliverypersonal.html')

@admin_required
@csrf_protect
def adminaddpersonnel(request):
    try:
        name = request.POST.get('personnelname')
        number = request.POST.get('personnelphonenumber')
        email = request.POST.get('personnelemail')
        photo = request.FILES.get('personnelimage')
        if not all([name, number, email]):
            return JsonResponse({'success': False, 'error': 'All fields are required.'}, status=400)

        if DeliveryPerson.objects.filter(phone_number=number).exists():
            return JsonResponse({'success': False, 'error': 'Delivery Personnel with this phone number already exists.'}, status=400)
        delivery_personnel = DeliveryPerson.objects.create_user(
            username=email,
            first_name=name,
            email=email,
            phone_number=number,
            profile_picture=photo,
            role='delivery_person',
            password= email,
            date_joined=timezone.localtime()
        )
        delivery_personnel_permission, created = Permission.objects.get_or_create(
            codename='is_deliveryperson',
            name='Can access delivery-specific features',
            content_type=ContentType.objects.get_for_model(DeliveryPerson)
        )
        delivery_personnel.user_permissions.add(delivery_personnel_permission)
        if delivery_personnel:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to create delivery personnel.'}, status=500)
    except Exception as e:
        print(f"Error in adminaddpersonnel view: {e}")
        return JsonResponse({'success': False, 'error': 'An error occurred. Please try again later.'}, status=500)

@require_http_methods(['GET']) 
@admin_required
@csrf_protect
def admin_get_delivery_personnels(request):
    if request.method == 'GET':
        try:
            delivery_personals = DeliveryPerson.objects.all()

            personnel_list = []
            for personnel in delivery_personals:
                personnel_data = {
                    'phone_number': personnel.phone_number,
                    'first_name': personnel.first_name.capitalize(),
                    'email': personnel.email,
                    'date_joined': timezone.localtime(personnel.date_joined).strftime('%d-%m-%Y'), 
                    'profile_picture': personnel.profile_picture.url if personnel.profile_picture else None
                }
                personnel_list.append(personnel_data)

            return JsonResponse({'success': True, 'data': personnel_list})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
@require_http_methods(["DELETE"])
@admin_required
@csrf_protect
def deletedeliverypersonnel(request):
    try:
        data=json.loads(request.body)
        phone_number=data.get('phone_number')
        if not phone_number: 
            return JsonResponse({'success': False, 'error': 'Phone number is required.'}, status=400)
        personnel = DeliveryPerson.objects.get(phone_number=phone_number)
        if personnel.profile_picture:
            image_path = personnel.profile_picture.path 
            if os.path.isfile(image_path):
                os.remove(image_path)
        personnel.delete()
        return JsonResponse({'success': True})
    except DeliveryPerson.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Delivery personnel not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["PUT"]) 
@admin_required
@csrf_protect
def updatedeliverypersonnel(request):
    try:
        data = json.loads(request.body)
        new_phone_number = data.get('phone_number')
        new_email = data.get('email')
        phone_number=data.get('old_number')
        personnel = DeliveryPerson.objects.get(phone_number=phone_number)
        personnel.phone_number = new_phone_number
        personnel.email = new_email
        personnel.save()

        return JsonResponse({'success': True})

    except DeliveryPerson.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Delivery personnel not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@admin_required
def adminmenu(request):
    return render(request,'adminmenu.html') 

@admin_required
@require_POST
@csrf_protect
def adminaddmenu(request):
    if request.method == 'POST':
        try:
            menu_name = request.POST.get('menuname')
            menu_image = request.FILES.get('menuimage')  
            if not all([menu_name, menu_image]): 
                return JsonResponse({'success': False, 'error': 'Required fields missing'})
            if Menu.objects.filter(menu_name=menu_name).exists():
                return JsonResponse({'success': False, 'error': f'{menu_name} already exists.'})
            menu = Menu.objects.create(
                menu_name=menu_name,
                menu_image=menu_image 
            )
            if menu:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'menu_group',
                    {
                        'type': 'menu_update',
                    }
                )
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Failed to create menu.'}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    
@admin_required
@require_http_methods(["GET"])
@csrf_protect
def admingetmenu(request):
    if request.method=='GET':
        try:
            menus = Menu.objects.all()
            menu_list = []
            for menu in menus:
                menu_data = {
                    'menu_id':menu.id,
                    'menu_name':menu.menu_name,
                    'menu_picture': menu.menu_image.url if menu.menu_image else None
                }
                menu_list.append(menu_data)
            
            return JsonResponse({'success': True, 'data': menu_list})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
@require_http_methods(["DELETE"])
@admin_required
@csrf_protect
def admindeletemenu(request):
    try:
        data = json.loads(request.body)
        menu_id = data.get('menu_id')
        if not menu_id:
            return JsonResponse({'success': False, 'error': 'Menu ID is required.'}, status=400)
        menu = Menu.objects.get(id=menu_id)
        if menu.menu_image:
            try:
                image_path = menu.menu_image.path 
                if os.path.isfile(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error deleting image: {e}")

        menu.delete()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'menu_group',
            {
                'type': 'menu_update',
            }
        )
        return JsonResponse({'success': True})

    except Menu.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Menu not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@admin_required
@require_POST
@csrf_protect
def adminupdatemenu(request):
    if request.method == 'POST':
        try:
            menu_id = request.POST.get('menu_id')
            menu = Menu.objects.get(pk=menu_id)
            image = request.FILES.get('menuimage')

            if image:
                if menu.menu_image: 
                    try:
                        old_image_path = os.path.join(settings.MEDIA_ROOT, str(menu.menu_image))
                        if os.path.isfile(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        print(f"Error deleting old image: {e}")

                menu.menu_image = image
                menu.save()
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'menu_group',
                    {
                        'type': 'menu_update',
                    }
                )
                return JsonResponse({'success': True}) 
            else:
                return JsonResponse({'success': False, 'error': 'No image provided.'})

        except Menu.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Menu not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@admin_required
def adminsubmenu(request):
    return render(request,'adminsubmenu.html')

@admin_required
@require_POST
@csrf_protect
def adminaddsubmenu(request):
    if request.method == 'POST':
        try:
            menu = request.POST.get('menu')
            sub_menu_name=request.POST.get('submenuname')
            sub_menu_image = request.FILES.get('submenuimage')  
            if not all([sub_menu_name, sub_menu_image]): 
                return JsonResponse({'success': False, 'error': 'Required fields missing'})
            try:
                menu=Menu.objects.get(id=menu)
            except Menu.DoesNotExist:
                return JsonResponse({'success':False,'error':'Menu Not found.'})
            if Menu.objects.filter(menu_name=sub_menu_name).exists():
                return JsonResponse({'success': False, 'error': f'{sub_menu_name} already exists.'})
            menu = SubMenu.objects.create(
                menu_name=menu,
                sub_menu_name=sub_menu_name,
                sub_menu_image=sub_menu_image 
            )
            if menu:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Failed to create menu.'}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
        
@admin_required
@require_http_methods(["GET"])
@csrf_protect
def admingetsubmenu(request):
    if request.method == 'GET':
        try:
            submenus = SubMenu.objects.select_related('menu_name').all() 
            submenu_data = [
                {
                    'sub_menu_id': submenu.id,
                    'sub_menu_name': submenu.sub_menu_name,
                    'menu_name': submenu.menu_name.menu_name, 
                    'sub_menu_image': submenu.sub_menu_image.url if submenu.sub_menu_image else None
                }
                for submenu in submenus
            ]
            return JsonResponse({'success': True, 'data': submenu_data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    
@admin_required
@require_POST
@csrf_protect
def adminupdatesubmenu(request):
    if request.method == 'POST':
        try:
            sub_menu_id = request.POST.get('submenu_id')
            sub_menu = SubMenu.objects.get(pk=sub_menu_id)
            image = request.FILES.get('submenuimage')

            if image:
                if sub_menu.sub_menu_image: 
                    try:
                        old_image_path = os.path.join(settings.MEDIA_ROOT, str(sub_menu.sub_menu_image))
                        if os.path.isfile(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        print(f"Error deleting old image: {e}")

                sub_menu.sub_menu_image = image
                sub_menu.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'No image provided.'})

        except SubMenu.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Menu not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    
@require_http_methods(["DELETE"])
@admin_required
@csrf_protect
def admindeletesubmenu(request):
    try:
        data = json.loads(request.body)
        sub_menu_id = data.get('sub_menu_id')
        if not sub_menu_id:
            return JsonResponse({'success': False, 'error': 'Sub Menu ID is required.'}, status=400)
        submenu = SubMenu.objects.get(id=sub_menu_id)
        if submenu.sub_menu_image:
            try:
                image_path = submenu.sub_menu_image.path 
                if os.path.isfile(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error deleting image: {e}")
        submenu.delete()
        return JsonResponse({'success': True})
    except Menu.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sub Menu not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@admin_required
def adminitems(request):
    return render(request,'adminitems.html')

@admin_required
@require_http_methods(["POST"])
@csrf_protect
def admingetsubmenusfordropdown(request):
    if request.method == 'POST':
        try:
            data=json.loads(request.body)
            menu_id=data.get('menu_id')
            menu=Menu.objects.get(id=menu_id)
            submenus = SubMenu.objects.filter(menu_name=menu)
            submenu_data = [{'sub_menu_id': submenu.id, 'sub_menu_name': submenu.sub_menu_name} for submenu in submenus]
            return JsonResponse({'success': True, 'data': submenu_data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    
@admin_required
@require_POST
@csrf_protect
def adminadditem(request):
    if request.method == 'POST':
        try:
            item_name = request.POST.get('itemname')
            description = request.POST.get('description')
            menu_id = request.POST.get('menu')
            submenu_id = request.POST.get('submenu')
            item_type = request.POST.get('type') 
            price = request.POST.get('price')
            is_available = request.POST.get('is_available')
            item_image = request.FILES.get('itemimage')
            preparation_time=request.POST.get('preparation_time')
            foodcourt=request.POST.get('foodcourt')
            itemquantity=request.POST.get('item-quantity')
            if is_available == 'on': 
                is_available = True
            elif is_available is None:
                is_available = False
            if not all([item_name, description, price]):
                return JsonResponse({'success': False, 'error': 'Item name, description, and price are required.'})
            if len(description) < 20:
                return JsonResponse({'success': False, 'error': 'Description must be at least 20 characters long.'})

            menu = Menu.objects.get(pk=menu_id) if menu_id else None
            submenu = SubMenu.objects.get(pk=submenu_id) if submenu_id else None
            restaurant=Restaurant.objects.get(email=foodcourt) if foodcourt else None

            item = Item.objects.create(
                menu=menu,
                submenu=submenu,
                item_name=item_name,
                description=description,
                type=item_type,  
                price=price,
                is_available=is_available,
                item_image=item_image,
                preparation_time=preparation_time,
                resturant=restaurant,
                count=itemquantity,
            )
            if item:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'allitems_group',
                    {
                        'type': 'items_update',
                    }
                )
                
                return JsonResponse({'success': True})
            
        except Menu.DoesNotExist:
            return JsonResponse({'success':False,'error':'Menu not exists.'})
        except SubMenu.DoesNotExist:
            return JsonResponse({'success':False,'error':'Submenu not exists.'})
        except Exception as e:
            return JsonResponse({'success':False,'error':str(e)})

@require_http_methods(["GET"])        
@admin_required
@csrf_protect
def admingetallitems(request):
    if request.method=='GET':
        try:
            items = Item.objects.select_related('menu', 'submenu').all()
            item_data = [
                {
                    'item_id': item.id,
                    'item_name':item.item_name,
                    'menu': item.menu.menu_name if item.menu else None, 
                    'submenu': item.submenu.sub_menu_name if item.submenu else None,
                    'description':item.description,
                    'restaurant':item.resturant.restaurant_name if item.resturant else None,
                    'type':item.type,
                    'price':item.price,
                    'is_avialable':item.is_available,
                    'preparation_time':item.preparation_time,
                    'item_image': item.item_image.url if item.item_image else None,
                    'count':item.count,
                }
                for item in items
            ]
            return JsonResponse({'success': True, 'data': item_data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@require_http_methods(["DELETE"])
@admin_required
@csrf_protect
def admindeleteitem(request):
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        if not item_id:
            return JsonResponse({'success': False, 'error': 'Item ID is required.'}, status=400)
        item = Item.objects.get(id=item_id)
        if item.item_image:
            try:
                image_path = item.item_image.path 
                if os.path.isfile(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error deleting image: {e}")
        item.delete()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'allitems_group',
            {
                'type': 'items_update',
            }
        )
        async_to_sync(channel_layer.group_send)(
            'cartitem_group',
            {
                'type': 'cart_update',
            }
        )
        return JsonResponse({'success': True})
    except Menu.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@admin_required
@require_POST
@csrf_protect
def adminupdateitem(request):
    if request.method == 'POST':
        channel_layer = get_channel_layer()
        try:
            data = json.loads(request.body)
            item_id=data.get('item_id')
            item_name = data.get('item_name')
            description = data.get('description')
            price = data.get('price')
            is_available = data.get('is_avialable')
            item_quantity=data.get('item_quantity')
            if not item_quantity:
                return JsonResponse({'success':False,'error':'Required quantity'})
            if is_available == 'on': 
                is_available = True
            elif is_available is None:
                is_available = False
            preparation_time = data.get('preparation_time')
            if not item_name:
                return JsonResponse({'success': False, 'error': 'Item name cannot be empty.'}, status=400)
            if len(description.split()) < 10: 
                return JsonResponse({'success': False, 'error': 'Description must be at least 20 words long.'}, status=400)

            item=Item.objects.get(id=item_id)
            item.item_name=item_name
            item.preparation_time=preparation_time
            item.description=description
            item.price=price
            item.is_available=is_available
            item.count=int(item_quantity)
            item.save()
            
            async_to_sync(channel_layer.group_send)(
                'cartitem_group',
                {
                    'type': 'cart_update',
                }
            )
            async_to_sync(channel_layer.group_send)(
                'search_items_group',
                {
                    'type': 'search_update',
                }
            )
            async_to_sync(channel_layer.group_send)(
                'search_items_group',
                {
                    'type': 'search_update',
                    'item_id': item.id,
                }
            )
            async_to_sync(channel_layer.group_send)(
                'allitems_group',
                {
                    'type': 'item_update',
                    'item_id': item.id,
                }
            )
            
            print(item_id)
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@admin_required
@require_POST
@csrf_protect
def adminupdateitemimage(request):
    if request.method == 'POST':
        try:
            item_id = request.POST.get('item_id')
            item = Item.objects.get(pk=item_id)
            itemimage = request.FILES.get('itemimage')

            if itemimage:
                if item.item_image:
                    try:
                        old_image_path = os.path.join(settings.MEDIA_ROOT, str(item.item_image))
                        if os.path.isfile(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        print(f"Error deleting old image: {e}")

                item.item_image = itemimage
                item.save()
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'allitems_group',
                    {
                        'type': 'item_update',
                        'item_id': item_id,
                    }
                )
                async_to_sync(channel_layer.group_send)(
                    'cartitem_group',
                    {
                        'type': 'cart_update',
                    }
                )
                async_to_sync(channel_layer.group_send)(
                    'search_items_group',
                    {
                        'type': 'search_update',
                        'item_id': item.id,
                    }
                )
               
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'No image provided.'})

        except Item.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Menu not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@admin_required
def adminpriceupdation(request):
    return render(request,'adminprice.html')

@admin_required
@require_POST
@csrf_protect
def adminaddprice(request):
    if request.method=='POST':
        try:
            pricetype = request.POST.get('pricetype')
            valuetype=request.POST.get('valuetype')
            description=request.POST.get('description')
            value = request.POST.get('value')  
            if not all([pricetype, valuetype,value]): 
                return JsonResponse({'success': False, 'error': 'Required fields missing'})
            if Prices.objects.filter(price_type=pricetype).exists():
                return JsonResponse({'success': False, 'error': f'{pricetype} already exists.'})
            price = Prices.objects.create(
                price_type=pricetype,
                value_type=valuetype,
                value=value,
                description=description, 
            )
            if price:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'cartitem_group',
                    {
                        'type': 'cart_update',
                    }
                )
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'addprices_group',
                    {
                        'type': 'addprices_update',
                    }
                )
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Failed to add additional price.'}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@require_http_methods(['GET'])
@admin_required
@csrf_protect
def admingetaddprices(request):
    if request.method=='GET':
        try:
            prices = Prices.objects.all() 
            prices_data = [
                {
                    'price_type': price.price_type,
                    'value_type': price.value_type,
                    'value': price.value, 
                    'description': price.description
                }
                for price in prices
            ]
            return JsonResponse(prices_data, safe=False)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    
@admin_required
@require_POST
@csrf_protect
def adminupdateprices(request):
    if request.method=='POST':
        data=json.loads(request.body)
        price_type=data.get('price_type')
        price=data.get('value')
        try:
            price_type=Prices.objects.get(price_type=price_type)
            if price_type:
                price_type.value=price
                price_type.save()
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'addprices_group',
                    {
                        'type': 'addprices_update',
                    }
                )
                return JsonResponse({'success':True})
            return JsonResponse({'success':False,'error':f'{price_type} not found.'})
        except Prices.DoesNotExist:
             return JsonResponse({'success':False,'error':f'{price_type} not found.'})
    return JsonResponse({'success':False,'error':'Invalid request method.'})

@require_http_methods(["DELETE"])
@admin_required
@csrf_protect
def admindeleteprice(request):
    if request.method=='DELETE':
        data=json.loads(request.body)
        price_type=data.get('price_type')
        try:
            price_type=Prices.objects.get(price_type=price_type)
            if price_type:
                price_type.delete()
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'addprices_group',
                    {
                        'type': 'addprices_update',
                    }
                )
                return JsonResponse({'success':True})
            return JsonResponse({'success':False,'error':f'{price_type} not found.'})
        except Prices.DoesNotExist:
             return JsonResponse({'success':False,'error':f'{price_type} not found.'})
    return JsonResponse({'success':False,'error':'Invalid request method.'})

@admin_required
def adminneworders(request):
    return render(request,'adminneworders.html')

@require_http_methods(["GET"])
@admin_required
@csrf_protect
def getneworder(request):
    if request.method == 'GET':
        orders = Order.objects.filter(status='confirmed', customer_status='confirmed').select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0 
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price  

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None 
                })

            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address':order.delivery_address,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price),  
                'total_item_price': str(item_total_price), 
                'total_additional_charges': str(total_additional_charges), 
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items, 
                'additional_charges': additional_charges_data,
                'restaurant_name':order.restaurant.restaurant_name,
                'daily_sequence':order.daily_sequence,  
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@admin_required
@require_POST
@csrf_protect
def adminconfirmorder(request):
    if request.method == 'POST':
        data=json.loads(request.body)
        order_id = data.get('order_id')
        if order_id:
            try:
                order = Order.objects.get(order_id=order_id)
                if order.status == 'pending':
                    order.status = 'confirmed' 
                    order.save()
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Order is not in pending state.'}) 
            except Order.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Order not found.'})
        else:
            return JsonResponse({'success': False, 'error': 'Order ID is missing.'}) 

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@admin_required
@require_POST
@csrf_exempt
def admincancelorder(request):
    try:
        data=json.loads(request.body)
        order_id = data.get('order_id')
        cancel_reason =data.get('cancel_reason')
        
        if not all([order_id, cancel_reason]):
            return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)
        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found.'}, status=404)

        if order.status == 'pending':
            order.status = 'cancelled'
            order.cancel_reason = cancel_reason
            order.cancelled_at=timezone.now()
            order.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Order is not in pending state.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@admin_required
def adminallorders(request):
    return render(request,'adminallorders.html')

@require_http_methods(["GET"])
@admin_required
@csrf_protect
def admingetallorder(request):
    if request.method == 'GET':
        orders = Order.objects.filter().select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0  
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price 

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None 
                })
            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address':order.delivery_address,
                'delivery_person': order.delivery_person.first_name if order.delivery_person else '-',
                'delivered_at': timezone.localtime(order.delivered_at).strftime('%d-%m-%Y %H:%M:%S') if order.delivered_at else None,
                'cancelled_at': timezone.localtime(order.cancelled_at).strftime('%d-%m-%Y %H:%M:%S') if order.cancelled_at else None,
                'cancel_reason':order.cancel_reason,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price), 
                'total_item_price': str(item_total_price),  
                'total_additional_charges': str(total_additional_charges),  
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data,
                'restaurant_name':order.restaurant.restaurant_name,
                'daily_sequence':order.daily_sequence,
            })
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@admin_required
def admindeliveredorders(request):
    return render(request,'admindeliveredorders.html')

@require_http_methods(['GET'])
@admin_required
@csrf_protect
def admingetdeliveredorders(request):
    if request.method == 'GET':
        orders = Order.objects.filter(status='delivered',customer_status='confirmed').select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0  
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price 

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None 
                })
            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address':order.delivery_address,
                'delivery_person': order.delivery_person.first_name if order.delivery_person else None,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price), 
                'total_item_price': str(item_total_price),  
                'total_additional_charges': str(total_additional_charges),  
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'delivered_at':timezone.localtime(order.delivered_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data,
                'restaurant_name':order.restaurant.restaurant_name,
                'daily_sequence':order.daily_sequence,  
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@admin_required
def admincancelledorders(request):
    return render(request,'admincancelledorders.html')

@require_http_methods(['GET'])
@admin_required
@csrf_protect
def admingetcancelledorders(request):
    if request.method == 'GET':
        orders = Order.objects.filter(status='cancelled',customer_status='confirmed').select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0  
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price 

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None 
                })
            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address':order.delivery_address,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price), 
                'total_item_price': str(item_total_price),  
                'total_additional_charges': str(total_additional_charges),  
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'cancelled_at':timezone.localtime(order.cancelled_at).strftime('%d-%m-%Y %H:%M:%S'),
                'cancel_reason':order.cancel_reason,
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data,
                'restaurant_name':order.restaurant.restaurant_name,
                'daily_sequence':order.daily_sequence,  
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@admin_required
def admindeliverylocations(request):
    return render(request,'admindeliverylocations.html')

@admin_required
@require_POST
@csrf_protect
def adminaddlocation(request):
    if request.method == 'POST':
        location_name = request.POST.get('locationname')
        location_image = request.FILES.get('locationimage')
        if not all([location_image, location_name]):
            return JsonResponse({'success': False, 'error': 'Invalid request. Missing fields.'})
        try:
            if DeliveryLocation.objects.filter(location_name=location_name).exists():
                return JsonResponse({'success': False, 'error': f'{location_name} already exists.'})
            location = DeliveryLocation.objects.create(location_name=location_name, location_image=location_image)
            if location:
                return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@require_http_methods(['GET'])
@admin_required
@csrf_protect
def admingetlocations(request):
    if request.method=='GET':
        try:
            locations = DeliveryLocation.objects.all()
            location_list = []
            for location in locations:
                location_data = {
                    'location_id':location.location_id,
                    'location_name':location.location_name,
                    'location_image': location.location_image.url if location.location_image else None
                }
                location_list.append(location_data)
            
            return JsonResponse({'success': True, 'data': location_list})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
@require_http_methods(['DELETE'])
@admin_required
@csrf_protect
def admindeletelocation(request):
    if request.method=='DELETE':
        data=json.loads(request.body)
        location_id=data.get('location_id')
        if not(location_id):
            return JsonResponse({'success':False,'error':'Required missing fields.'})
        try:
            location=DeliveryLocation.objects.filter(location_id=location_id)
            location.delete()
            return JsonResponse({'success':True})
        except Exception as e:
            return JsonResponse({'success':False,'error':str(e)})
    return JsonResponse({'success':False,'error':'Invalid request method.'})

@admin_required
def adminallusers(request):
    return render(request,'adminallusers.html')

@require_http_methods(['GET'])
@admin_required
@csrf_protect
def admingetallusers(request):
    if request.method == 'GET':
        users = CustomUser.objects.filter().values('email', 'phone_number', 'role', 'first_name', 'last_name')
        users_list = list(users)
        
        return JsonResponse({'users': users_list}, safe=False)
    return JsonResponse({'success':False,'error':'Invalid request method.'})

@require_http_methods(["DELETE"])
@admin_required
@csrf_protect
def admindeleteuser(request):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            email_id = data.get('user_id')
            if not email_id:
                return JsonResponse({'success': False, 'error': 'User Id not provided.'})
            user = CustomUser.objects.get(email__iexact=email_id)
            user.delete()
            return JsonResponse({'success': True, 'message': 'User deleted successfully.'})
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User does not exist.'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON format.'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@admin_required
def adminassignorder(request):
    return render(request,'adminassignorder.html')

@require_http_methods(["GET"])
@admin_required
@csrf_protect
def admingettobeassignedorders(request):
    if request.method == 'GET':
        orders = Order.objects.filter(status='confirmed',delivery_type='delivery',customer_status='confirmed').select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0  
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price 

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None 
                })
            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address':order.delivery_address,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price), 
                'total_item_price': str(item_total_price),  
                'total_additional_charges': str(total_additional_charges),  
                'status': order.get_status_display(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'cancelled_at':timezone.localtime(order.cancelled_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data,
                'restaurant_name':order.restaurant.restaurant_name  ,
                'daily_sequence':order.daily_sequence,
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@require_http_methods(['GET']) 
@admin_required
@csrf_protect
def admin_get_delivery_personnels_performance(request):
    if request.method == 'GET':
        try:
            delivery_personals = DeliveryPerson.objects.all()

            personnel_list = []
            for personnel in delivery_personals:
                total_orders_assigned = Order.objects.filter(delivery_person=personnel).count()
                orders_delivered = Order.objects.filter(delivery_person=personnel, status='delivered').count()

                personnel_data = {
                    'phone_number': personnel.phone_number,
                    'first_name': personnel.first_name.capitalize(),
                    'email': personnel.email,
                    'date_joined': timezone.localtime(personnel.date_joined).strftime('%d-%m-%Y'),
                    'total_orders_assigned': total_orders_assigned,
                    'orders_delivered': orders_delivered,
                }
                personnel_list.append(personnel_data)

            return JsonResponse({'success': True, 'data': personnel_list})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@require_http_methods(['GET'])
@admin_required
@csrf_protect
def admin_get_delivery_personnel_performance_chart_data(request):
    email = request.GET.get('email')
    if email:
        try:
            personnel = DeliveryPerson.objects.get(email=email)
            today = timezone.now().date()
            
            last_7_days_data = []
            for i in range(7):
                date = today - timedelta(days=i)
                delivered_orders = Order.objects.filter(
                    delivery_person=personnel,
                    created_at__date=date,
                    status='delivered'
                ).count()
                last_7_days_data.append({'date': date.strftime('%Y-%m-%d'), 'count': delivered_orders})
            
            last_5_weeks_data = []
            for i in range(5):
                start_date = today - timedelta(weeks=i+1)
                end_date = today - timedelta(weeks=i)
                delivered_orders = Order.objects.filter(
                    delivery_person=personnel,
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date,
                    status='delivered'
                ).count()
                last_5_weeks_data.append({'week': start_date.strftime('%Y-%m-%d'), 'count': delivered_orders})

            last_12_months_data = []
            for i in range(12):
                year = today.year - i
                if i == 0:
                    month = today.month
                else:
                    month = 12
                start_date = timezone.datetime(year, month, 1)
                end_date = timezone.datetime(year, month, 1) + timedelta(days=31)
                delivered_orders = Order.objects.filter(
                    delivery_person=personnel,
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date,
                    status='delivered'
                ).count()
                last_12_months_data.append({'month': start_date.strftime('%Y-%m'), 'count': delivered_orders})

            context = {
                'last_7_days_data': list(reversed(last_7_days_data)),
                'last_5_weeks_data': list(reversed(last_5_weeks_data)),
                'last_12_months_data': list(reversed(last_12_months_data))
            }

            return JsonResponse({'success': True, 'context': context})

        except DeliveryPerson.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Delivery Personnel not found.'}, status=404)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Missing email parameter.'}, status=400)

@admin_required
@require_POST
@csrf_protect
def adminassignordertodelivery(request):
    data = json.loads(request.body)
    order_id = data.get('order_id')
    delivery_personnel_email = data.get('delivery_personnel')
    if not all([order_id, delivery_personnel_email]):
        return JsonResponse({'success': False, 'error': 'Required missing fields.'})
    try:
        delivery_personnel = DeliveryPerson.objects.get(email=delivery_personnel_email)
    except DeliveryPerson.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Delivery Personnel not exists.'})
    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not exists.'})

    try:
        order.delivery_person = delivery_personnel
        order.status = 'shipped'
        order.save()
        print(delivery_personnel.id)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'delivery_person_{delivery_personnel.id}',
            {
                "type": 'new_order',
                "order_id": order.order_id
            }
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@admin_required
def admindeliveryperformance(request):
    return render(request,'admindeliveryperformance.html')

@admin_required
def admincustomerprofile(request):
    return render(request,'admincutomerprofile.html')

@admin_required
def adminorderhistory(request):
    return render(request,'adminorderhistory.html')

@require_http_methods(['GET'])
@admin_required
@csrf_exempt
def admingetcustomerorders(request,email):
    if request.method == 'GET':
        user = CustomUser.objects.get(email=email)
        orders = Order.objects.filter(user=user).select_related('user', 'payment').prefetch_related('items').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            for order_item in order.orderitem_set.all():
                item = order_item.item
                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),
                    'type': item.get_type_display(),
                    'item_image': item.item_image.url if item.item_image else None
                })

            order_data.append({
                'order_id': order.order_id,
                'total_price': str(order.total_price),
                'status': order.get_status_display(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'items': order_items
            })
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@require_http_methods(['GET'])
@admin_required
@csrf_protect
def admingetorderdetails(request,order_id):
    if request.method == 'GET':
        orders = Order.objects.filter(order_id=order_id).select_related('user', 'payment').prefetch_related('items', 'additional_charges')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0  
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price 

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'description':item.description,
                    'item_image': item.item_image.url if item.item_image else None 
                })
            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'delivery_address':order.delivery_address,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price), 
                'total_item_price': str(item_total_price),  
                'total_additional_charges': str(total_additional_charges),  
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data,
                'restaurant_name':order.restaurant.restaurant_name,
                'daily_sequence':order.daily_sequence,    
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@admin_required
def adminsalesreports(request):
    return render(request,'adminsalesreports.html')

@require_http_methods(['GET'])
@admin_required
@csrf_protect
def top_ordered_customers(request):
    top_customers = (CustomUser.objects.annotate(
        total_orders=Count('order', distinct=True),
        cancelled_orders=Count(
            Case(When(order__status='cancelled', then=1)),
            distinct=True
        ),
        delivered_orders=Count(
            Case(When(order__status='delivered', then=1)),
            distinct=True
        ),
        revenue_generated=Sum(F('order__total_price'))
    ).filter(total_orders__gt=0)
    .order_by('-total_orders')[:10]
    )

    customer_data = [
        {
            'email': customer.email,
            'name': f"{customer.first_name} {customer.last_name}",
            'total_orders': customer.total_orders,
            'cancelled_orders': customer.cancelled_orders,
            'delivered_orders': customer.delivered_orders,
            'revenue_generated': customer.revenue_generated,
        } for customer in top_customers
    ]

    return JsonResponse({'success': True, 'data': customer_data})

@admin_required
def adminresturants(request):
    return render(request,'adminresturant.html')

@admin_required
@require_POST
@csrf_protect
def adminaddresturant(request):
    if request.method=='POST':
        restaurant_name = request.POST.get('foodcourtname')
        foodcourtemail=request.POST.get('foodcourtemail')
        restaurant_image = request.FILES.get('resturantimage')
        if not all([restaurant_name, restaurant_image,foodcourtemail]):
            return JsonResponse({'success': False, 'error': 'Required Missing fields.'})
        hashed_password=make_password(f'{restaurant_name}#@0987612345')
        try:
            if Restaurant.objects.filter(email=foodcourtemail).exists():
                return JsonResponse({'success': False, 'error': f'{foodcourtemail} already exists.'})
            restaurant = Restaurant.objects.create(
                username=foodcourtemail,
                email=foodcourtemail,
                first_name=restaurant_name,
                restaurant_name=restaurant_name,
                restaurant_image=restaurant_image,
                password=hashed_password,
                role='restaurant',
            )    
            restaurant_permission, created = Permission.objects.get_or_create(
                codename='is_restaurant',
                name='Can access restaurant-specific features',
                content_type=ContentType.objects.get_for_model(Restaurant)
            )
            restaurant.user_permissions.add(restaurant_permission)
            if restaurant:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Failed to add restaurant.'}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@require_http_methods(['GET'])
@admin_required
@csrf_protect
def admingetresturant(request):
    if request.method=='GET':
        try:
            restaurants = Restaurant.objects.all() 
            restaurant_data = [
                {
                    'resturant_id': restaurant.email,
                    'resturant_name': restaurant.restaurant_name,
                    'resturant_image': restaurant.restaurant_image.url if restaurant.restaurant_image else None, 
                }
                for restaurant in restaurants
            ]
            return JsonResponse({'success': True, 'data': restaurant_data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@admin_required
@require_POST
@csrf_protect
def adminupdateresturantimage(request):
    if request.method == 'POST':
        try:
            restaurant_id = request.POST.get('resturant_id')
            image = request.FILES.get('resturant_image')
            restaurant = Restaurant.objects.get(email=restaurant_id)
            if image:
                if restaurant.restaurant_image: 
                    try:
                        old_image_path = os.path.join(settings.MEDIA_ROOT, str(restaurant.restaurant_image))
                        if os.path.isfile(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        print(f"Error deleting old image: {e}")

                restaurant.restaurant_image = image
                restaurant.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'No image provided.'})

        except Restaurant.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Restaurant not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    
@require_http_methods(["DELETE"])
@admin_required
@csrf_protect
def admindeleteresturant(request):
    try:
        data = json.loads(request.body)
        resturant_id = data.get('resturant_id')
        if not resturant_id:
            return JsonResponse({'success': False, 'error': 'Resturant Id is required.'}, status=400)
        resturant = Restaurant.objects.get(email=resturant_id)
        if resturant.restaurant_image:
            try:
                image_path = resturant.restaurant_image.path 
                if os.path.isfile(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error deleting image: {e}")
        resturant.delete()
        return JsonResponse({'success': True})
    except Menu.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sub Menu not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


USER_NOTIFICATION_MESSAGES = {
     'pending': [("Your order is awaiting confirmation!", "⏳"),
        ("We've received your order, processing it now!", "🕒"),
        ("We're waiting on finalization for your order!", "📝")],
    'confirmed': [("Your order has been confirmed!","✅"),
     ("Great news! Your order is confirmed!", "🎉"),
      ("We're ready to prepare your order!", "👍")],
    'prepared': [("Your order is being prepared!", "🍳"),
        ("Your order is being carefully prepared!", "👨‍🍳"),
         ("The kitchen is cooking up your order!", "🔥")],
    'shipped': [("Your order is on its way!","🚚"),
         ("Your order is in transit!", "📦"),
         ("Your order is heading out for delivery!", "🌍")],
    'delivered': [("Your order has been delivered!", "🥳"),
     ("Order completed, hope you enjoyed!", "✔️"),
      ("Your order is completed, delivered successfully!", "🙌")],
     'preparing': [("Your order is being prepared!", "👨‍🍳"),
        ("The kitchen is preparing your order!", "🔥"),
        ("We're getting your order ready for pickup!", "🍜")],
    'ready_to_take': [("Your order is ready for pickup!", "🛍️"),
    ("Time to pick up your order!", "📍"),
     ("You can take your order now!", "👍")],
    'cancelled': [("Your order has been cancelled!", "❌"),
       ("We had to cancel your order, sorry for the inconvenience", "⚠️"),
        ("There has been a problem, and we had to cancel your order", "🚫")],
    
}

def get_status_index(delivery_type, status):
        if delivery_type == 'delivery':
            status_list=['pending', 'confirmed', 'prepared', 'shipped', 'delivered', 'cancelled']
            return status_list.index(status) if status in status_list else -1
        elif delivery_type == 'pickup':
           status_list= ['pending', 'confirmed', 'preparing', 'ready_to_take', 'delivered', 'cancelled']
           return status_list.index(status) if status in status_list else -1
        elif delivery_type == 'dining':
             status_list=['pending', 'confirmed', 'preparing', 'delivered', 'cancelled']
             return status_list.index(status) if status in status_list else -1
        return -1

@require_POST
@admin_required
@csrf_protect
def adminupdateorderstatus(request):
    channel_layer=get_channel_layer()
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        status = data.get('status')
    except json.JSONDecodeError:
      return JsonResponse({'success': False, 'error': 'Invalid JSON format in request body'}, status=400)
    if request.method == 'POST':
        try:
            order = Order.objects.get(order_id=order_id)
            
            status_map = {
                "Ordered": "pending",
                "Confirmed": "confirmed",
                "Prepared": "prepared",
                "Shipped": "shipped",
                "Delivered": "delivered",
                "Preparing":"preparing",
                "Ready to Take": "ready_to_take",
                "Received by Customer": "delivered",
                "Served":"delivered",
                "Cancelled":"cancelled",
                "Served to Customer":"delivered",
            }
            if status in status_map:
                status = status_map[status]
            else:
                return JsonResponse({'success': False, 'error': 'Invalid status label received.'}, status=400)

            all_status_choices = [val for val, label in dict(Order.DELIVERY_STATUS_CHOICES + Order.PICKUP_STATUS_CHOICES + Order.DINING_STATUS_CHOICES).items() ]
            if status not in all_status_choices:
               return JsonResponse({'success': False, 'error': 'Invalid status value.'}, status=400)

            current_status_index = get_status_index(order.delivery_type, order.status)
            new_status_index=get_status_index(order.delivery_type, status)

            if new_status_index <= current_status_index and order.status != 'cancelled':
                return JsonResponse({'success': False, 'error': 'Cannot revert back to a previous status'}, status=400)


            order.status = status
            order.save()
            async_to_sync(channel_layer.group_send)(
                    'admin_group',
                    {
                        "type": 'admin_all_order'
                    }
             )
            async_to_sync(channel_layer.group_send)(
                    'restaurant_group',
                    {
                        "type": 'restaurant_all_order'
                    }
            )
            async_to_sync(channel_layer.group_send)(
                'delivery_group',
                {
                    "type": 'delivery_new_order'
                }
            )
            async_to_sync(channel_layer.group_send)(
                'delivery_group',
                {
                   "type": 'delivery_delivered_order'
                }
            )
        
            async_to_sync(channel_layer.group_send)(
                'admin_group',
                {
                    "type": 'admin_delivered_order'
                }
            ) 
            async_to_sync(channel_layer.group_send)(
                'restaurant_group',
                {
                    "type": 'restaurant_new_order'
                }
            ) 
            async_to_sync(channel_layer.group_send)(
                'restaurant_group',
                {
                    "type": 'restaurant_delivered_order'
                }
            )
            async_to_sync(channel_layer.group_send)(
                    'admin_group',
                    {
                        "type": 'admin_new_order'
                    }
            )
            try:
               
                user = order.user
                message,emoji = choice(USER_NOTIFICATION_MESSAGES.get(status,'no notification'))
                notification_message=f"{message} Order ID: {order.order_id} {emoji}"
                user_notification = UserNotification.objects.create(
                    user=user,
                    title='Order Status Updated',
                    message=notification_message,
                    related_order=order
                )
                print('sending notification')
                notification_data = {
                    'user_ids': user.email,
                    'title': 'Order Update',
                    'body': notification_message,
                 }
                notification_response = send_notification_helper(notification_data)
                if notification_response.status_code != 200:
                     print(f"Error sending notification: {notification_response.content}")

            except Exception as e:
                print(f"Error sending notification: {e}")


            return JsonResponse({'success': True})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid order'}, status=404)
        except ValidationError as e:
          return JsonResponse({'success':False, 'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@admin_required
@require_POST
@csrf_protect
def adminorderdetails(request):
    if request.method=='POST':
        data=json.loads(request.body)
        order_id=data.get('order_id')
        try:
            order=Order.objects.get(order_id=order)

        except Order.DoesNotExist:
            return JsonResponse({'success':False,'error':'Invalid order'})
        
@admin_required
def adminlogout(request):
    logout(request)
    return redirect('adminlogin')

#users

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

            if user.role == 'restaurant':
                return JsonResponse({'success': False, 'error': 'Invalid Email'})

            
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
                'user_name': user.first_name,
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
            username=data.get('username')
            phone_number=data.get('phone_number')
            User = get_user_model()
            try:
                verification = EmailVerification.objects.get(email=email)

                if verification.is_expired():
                    return JsonResponse({'success': False, 'error': 'Verification code has expired.'})

                if verification.verification_code == entered_code:
                    verification.is_verified = True
                    verification.save()
                    user=RegularUser.objects.create(
                        username=email,
                        email=email,
                        phone_number=phone_number,
                        role='user',
                        first_name=username,
                    )
                    user.save()
                    user_permission, created = Permission.objects.get_or_create(
                    codename='is_user',
                    name='Can access user-specific features',
                    content_type=ContentType.objects.get_for_model(RegularUser)
                    )
                    user.user_permissions.add(user_permission)
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
def sendsignverificationcode(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            User = get_user_model()
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'User already exists.'})
            verification_code = ''.join(random.choice(string.digits) for _ in range(6))
            expiration_time = timezone.now() + timezone.timedelta(minutes=10)

            try:
                verification, created = EmailVerification.objects.get_or_create(email=email)
                if created:  
                    verification.email = email 
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

@require_http_methods(["GET"])
@user_required
@csrf_exempt
def getmenu(request):
    if request.method == 'GET':
        try:
            menus = Menu.objects.all()
            menu_list = []
            for menu in menus:
                items = Item.objects.filter(menu=menu).order_by('price')[:4]
                item_data = [
                    {
                       'item_id': item.id,
                        'item_name': item.item_name,
                        'item_image': item.item_image.url if item.item_image else None,
                         'price':float(item.price)
                    }
                    for item in items
                ]
                min_price_item = Item.objects.filter(menu=menu).aggregate(min_price=Min('price'))
                
                menu_data = {
                    'menu_id': menu.id,
                    'menu_name': menu.menu_name,
                    'menu_picture': menu.menu_image.url if menu.menu_image else None,
                    'items':item_data,
                    'min_price':float(min_price_item['min_price']) if min_price_item['min_price'] else None,
                }
                menu_list.append(menu_data)

            return JsonResponse({'success': True, 'data': menu_list})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
@require_http_methods(["GET"])
@user_required
@csrf_protect
def getallitems(request):
    try:
        items = Item.objects.select_related('menu', 'submenu','resturant').order_by('-is_available')
        cart_items = Cart.objects.filter(user=request.user)
        cart_dict = {cart_item.item_id: cart_item.quantity for cart_item in cart_items}
        
        item_data = [
            {
                'item_id': item.id,
                'item_name': item.item_name,
                'menu': item.menu.menu_name if item.menu else None,
                'submenu': item.submenu.sub_menu_name if item.submenu else None,
                'description': item.description,
                'type': item.type,
                'price': float(item.price), 
                'is_available': item.is_available,
                'preparation_time': item.preparation_time,
                'item_image': item.item_image.url if item.item_image else None,
                'in_cart': item.id in cart_dict,  
                'quantity': cart_dict.get(item.id, 0),
                'resturant_name':item.resturant.restaurant_name,
                'count':item.count,
            }
            for item in items
        ]
        
        return JsonResponse({'success': True, 'data': item_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@require_http_methods(['GET'])
@user_required
@csrf_protect
def filter_items(request):
    if request.method=='GET':
        items = Item.objects.select_related('menu', 'submenu').all()

        sort_option = request.GET.get('sort', 'relevance')
        ratings = request.GET.get('ratings', '').split(',')  
        veg_non_veg = request.GET.get('vegNonVeg')
        price_range = request.GET.get('price')

        if sort_option == 'deliveryTime':
            items = items.order_by('preparation_time') 
        elif sort_option == 'rating':
            items = items.order_by('-rating')
        elif sort_option == 'lowToHigh':
            items = items.order_by('price')
        elif sort_option == 'highToLow':
            items = items.order_by('-price')

        if ratings:
            ratings = [float(r) for r in ratings if r]  
            if ratings:  
                items = items.filter(rating__gte=min(ratings, default=4.0))

        if veg_non_veg == 'veg':
            items = items.filter(type='veg') 
        elif veg_non_veg == 'nonVeg':
            items = items.filter(type='non_veg') 

        if price_range:
            try:
                price = float(price_range) 
                items = items.filter(price__lte=price) 
            except ValueError:
                pass 
        
        cart_items = Cart.objects.filter(user=request.user)
        cart_dict = {cart_item.item_id: cart_item.quantity for cart_item in cart_items}
        items_data = [
            {
                'item_id': item.id,
                'item_name': item.item_name,
                'menu': item.menu.menu_name if item.menu else None,
                'submenu': item.submenu.sub_menu_name if item.submenu else None,
                'description': item.description,
                'type': item.type,
                'price': float(item.price), 
                'is_available': item.is_available,
                'preparation_time': item.preparation_time,
                'item_image': item.item_image.url if item.item_image else None,
                'in_cart': item.id in cart_dict,  
                'quantity': cart_dict.get(item.id, 0),
                'resturant_name':item.resturant.restaurant_name,
            }
            for item in items 
        ]

        return JsonResponse({'items': items_data})


@user_required
def checkout(request):
    return render(request,'checkout.html')

@require_http_methods(["GET"])
@user_required
@csrf_protect
def get_cart_items(request):
    email = request.session.get('email')
    if not email:
        return JsonResponse({'success': False, 'error': 'User not authenticated.'})
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User does not exist.'})
    cart_items = Cart.objects.filter(user=user).select_related('item')
    available_cart_items = [
        {
            'id': item.id,
            'product_name': item.item.item_name, 
            'quantity': item.quantity,
            'price': item.item.price  
        }
        for item in cart_items if item.item.is_available 
    ]
    return JsonResponse({'success': True, 'cart_items': available_cart_items})

@user_required
@require_POST
@csrf_protect
def update_cart_item(request):
    if request.method == 'POST':
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'User not authenticated.'})
        operation = request.POST.get('operation')
        item_id = request.POST.get('item_id')

        try:
            cart_item = Cart.objects.get(user=user, item_id=item_id)
        except Cart.DoesNotExist:
            try:
                item = Item.objects.get(id=item_id)
                cart_item = Cart.objects.create(user=user, item=item, quantity=1)
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'cartitem_group',
                    {
                        'type': 'cart_update',
                    }
                )
                async_to_sync(channel_layer.group_send)(
                    'addprices_group',
                    {
                        'type': 'addprices_update',
                    }
                )
                return JsonResponse({'success':True})
            except Item.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Item does not exist.'})
        if operation == 'increment':
            item = Item.objects.get(id=item_id)
            if cart_item.quantity >= item.count:
                 return JsonResponse({
                    'success': False,
                    'error': f'Insufficient stock for {item.item_name}',
                    'count': item.count,
                    'quantity': cart_item.quantity
                },
            )
            cart_item.quantity += 1
        elif operation == 'decrement':
            cart_item.quantity -= 1
            if cart_item.quantity <= 0:
                cart_item.delete()
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'cartitem_group',
                    {
                        'type': 'cart_update',
                    }
                )
                async_to_sync(channel_layer.group_send)(
                    'addprices_group',
                    {
                        'type': 'addprices_update',
                    }
                )
                return JsonResponse({'success': True, 'removed': True, 'message': 'Item removed from cart'})
        if cart_item.pk:
            cart_item.save()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'cartitem_group',
            {
                'type': 'cart_update',
            }
        )
        async_to_sync(channel_layer.group_send)(
            'addprices_group',
            {
                'type': 'addprices_update',
            }
        )
        return JsonResponse({'success': True, 'quantity': cart_item.quantity, 'total_price': cart_item.item.price * cart_item.quantity})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@require_POST
@csrf_protect
def add_to_cart(request):
    if request.method == 'POST':
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'User not authenticated.'})
        operation = request.POST.get('operation')
        item_id = request.POST.get('item_id')
        replace_cart = request.POST.get('replace_cart')
        try:
            item = Item.objects.get(id=item_id)
            restaurant = item.resturant 
            existing_cart_items = Cart.objects.filter(user=user)
            if existing_cart_items.exists():
                first_restaurant = existing_cart_items.first().item.resturant
                if restaurant != first_restaurant:
                    if replace_cart and replace_cart.lower() == 'true':
                        existing_cart_items.delete()
                        try:
                            item = Item.objects.get(id=item_id)
                            cart_item = Cart.objects.create(user=user, item=item, quantity=1)
                            channel_layer = get_channel_layer()
                            async_to_sync(channel_layer.group_send)(
                                'allitems_group',
                                {
                                    'type': 'items_update',
                                }
                            )
                            async_to_sync(channel_layer.group_send)(
                                'cartitem_group',
                                {
                                    'type': 'cart_update',
                                }
                            )
                            async_to_sync(channel_layer.group_send)(
                                'addprices_group',
                                {
                                    'type': 'addprices_update',
                                }
                            )
                            async_to_sync(channel_layer.group_send)(
                                'search_items_group',
                                {
                                    'type': 'search_update',
                                     'item_id': item.id,
                                }
                            )
                            
                            return JsonResponse({'success':True})
                        except Item.DoesNotExist:
                            return JsonResponse({'success': False, 'error': 'Item does not exist.'})  
                    else:
                        return JsonResponse({
                            'success': False,
                            'replace_cart': True,
                            'restaurant_name': restaurant.restaurant_name,
                            'current_restaurant_name': first_restaurant.restaurant_name,
                            'item_id':item_id,
                            'operation':operation
                        })

            try:
                cart_item = Cart.objects.get(user=user, item_id=item_id)
            except Cart.DoesNotExist:
                try:
                    item = Item.objects.get(id=item_id)
                    cart_item = Cart.objects.create(user=user, item=item, quantity=1)
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        'allitems_group',
                        {
                            'type': 'item_update',
                            'item_id': item.id,
                        }
                    )
                    async_to_sync(channel_layer.group_send)(
                        'cartitem_group',
                        {
                            'type': 'cart_update',
                        }
                    )
                    async_to_sync(channel_layer.group_send)(
                        'addprices_group',
                        {
                            'type': 'addprices_update',
                        }
                    )
                    async_to_sync(channel_layer.group_send)(
                        'search_items_group',
                        {
                            'type': 'search_update',
                            'item_id': item.id,
                        }
                    )
                    return JsonResponse({'success':True})
                except Item.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Item does not exist.'})    
            if operation == 'increment':
                if cart_item.quantity >= item.count:
                    return JsonResponse({
                        'success': False,
                        'error': f'Insufficient stock for {item.item_name}',
                        'count': item.count,
                        'quantity': cart_item.quantity
                    },
                )
                cart_item.quantity += 1
            elif operation == 'decrement':
                cart_item.quantity -= 1
                if cart_item.quantity <= 0:
                    cart_item.delete()
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        'allitems_group',
                        {
                            'type': 'item_update',
                            'item_id': item.id,
                        }
                    )
                    async_to_sync(channel_layer.group_send)(
                        'cartitem_group',
                        {
                            'type': 'cart_update',
                        }
                    )
                    async_to_sync(channel_layer.group_send)(
                        'addprices_group',
                        {
                            'type': 'addprices_update',
                        }
                    )
                    async_to_sync(channel_layer.group_send)(
                        'search_items_group',
                        {
                            'type': 'search_update',
                            'item_id': item.id,
                        }
                    )
                    return JsonResponse({'success': True, 'removed': True, 'message': 'Item removed from cart'})
            if cart_item.pk:
                cart_item.save()
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'allitems_group',
                {
                    'type': 'item_update',
                    'item_id': item.id,
                }
            )
            async_to_sync(channel_layer.group_send)(
                'cartitem_group',
                {
                    'type': 'cart_update',
                }
            )
            async_to_sync(channel_layer.group_send)(
                'addprices_group',
                {
                    'type': 'addprices_update',
                }
            )
            async_to_sync(channel_layer.group_send)(
                'search_items_group',
                {
                    'type': 'search_update',
                     'item_id': item.id,
                }
            )
            return JsonResponse({'success': True, 'quantity': cart_item.quantity, 'total_price': cart_item.item.price * cart_item.quantity})
        except Item.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item does not exist.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@user_required
def profile(request):
    return render(request,'profile.html')

@user_required
@require_POST
@csrf_protect
def addphonenumber(request):
    if request.method == 'POST':
        user = request.user
        new_phone_number = request.POST.get('phone_number')

        if not new_phone_number or len(new_phone_number) != 10 or not new_phone_number.isdigit():
            return JsonResponse({'success': False, 'message': 'Invalid phone number'})

        user.phone_number = new_phone_number
        user.save()

        return JsonResponse({'success': True, 'message': 'Phone number updated successfully'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})
    
@user_required
@require_POST
@csrf_protect
def updatemobilenumber(request):
    if request.method == 'POST':
        user = request.user
        new_phone_number = request.POST.get('mobileNumber')

        if not new_phone_number or len(new_phone_number) != 10 or not new_phone_number.isdigit():
            return JsonResponse({'success': False, 'message': 'Invalid phone number'})

        user.phone_number = new_phone_number
        user.save()

        return JsonResponse({'success': True, 'message': 'Phone number updated successfully'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})

@require_http_methods(['GET'])
@user_required
@csrf_exempt
def getorders(request):
    if request.method == 'GET':
        user = request.user
        orders = Order.objects.filter(user=user).select_related('user', 'payment').prefetch_related('items').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            for order_item in order.orderitem_set.all():
                item = order_item.item
                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),
                    'type': item.get_type_display(),
                    'item_image': item.item_image.url if item.item_image else None
                })

            order_data.append({
                'order_id': order.order_id,
                'total_price': str(order.total_price),
                'status': order.get_status_display(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'items': order_items
            })
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@user_required
def orderhistory(request):
    return render(request,'orderhistory.html')

@require_http_methods(['GET'])
@user_required
@csrf_protect
def getorderdetails(request,order_id):
    if request.method == 'GET':
        orders = Order.objects.filter(order_id=order_id).select_related('user', 'payment').prefetch_related('items', 'additional_charges')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0  
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price 

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'description':item.description,
                    'item_image': item.item_image.url if item.item_image else None 
                })
            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'delivery_address':order.delivery_address,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price), 
                'total_item_price': str(item_total_price),  
                'total_additional_charges': str(total_additional_charges),  
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data  
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@user_required
def search(request):
    return render(request,'search.html')

@user_required
def search_items(request):
    query = request.GET.get('q', '').strip()
    if query:
        search_terms = query.lower().split()
        q_objects = Q()
        for i in range(1, len(search_terms) + 1):
           for j in range(len(search_terms) - i + 1):
               phrase = " ".join(search_terms[j:j + i])
               q_objects |= Q(item_name__icontains=phrase) | Q(menu__menu_name__icontains=phrase) |  Q(submenu__sub_menu_name__icontains=phrase) | Q(resturant__restaurant_name__icontains=phrase)
        items = Item.objects.filter(q_objects).select_related('menu', 'submenu','resturant').distinct().order_by('-is_available')
        cart_items = Cart.objects.filter(user=request.user)
        cart_dict = {cart_item.item_id: cart_item.quantity for cart_item in cart_items}

        items_data = [
            {
                'item_id': item.id,
                'item_name': item.item_name,
                'menu': item.menu.menu_name if item.menu else None,
                'submenu': item.submenu.sub_menu_name if item.submenu else None,
                'description': item.description,
                'type': item.type,
                'price': float(item.price),
                'is_available': item.is_available,
                'preparation_time': item.preparation_time,
                'item_image': item.item_image.url if item.item_image else None,
                'in_cart': item.id in cart_dict,
                'quantity': cart_dict.get(item.id, 0),
                'resturant_name':item.resturant.restaurant_name,
            }
            for item in items
        ]

        return JsonResponse({'items': items_data})
    else:
        return JsonResponse({'items': []}) 
    
@require_http_methods(['GET'])
@user_required
@csrf_protect
def getlocations(request):
    if request.method=='GET':
        try:
            locations = DeliveryLocation.objects.all()
            location_list = []
            for location in locations:
                location_data = {
                    'location_id':location.location_id,
                    'location_name':location.location_name,
                    'location_image': location.location_image.url if location.location_image else None
                }
                location_list.append(location_data)
            
            return JsonResponse({'success': True, 'data': location_list})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@user_required
def user_logout_view(request):
    logout(request)
    return redirect('index')

@require_http_methods(['POST'])
@csrf_protect
@user_required
def updatedelivery_type(request):
    channel_layer = get_channel_layer()
    try:
        user = request.user
        data = json.loads(request.body)
        delivery_type = data.get('deliveryType')

        if not user.is_authenticated:
             print("User not authenticated.")
             return JsonResponse({'success': False, 'error': 'User not authenticated.'})

        update_delivery = CustomUser.objects.get(email=user)
        if user:
            update_delivery.delivery_type = delivery_type
            update_delivery.save()
            print("Delivery type updated:", update_delivery.delivery_type)

            print("Before cartitem_group send")
            async_to_sync(channel_layer.group_send)(
                'cartitem_group',
                {
                    'type': 'cart_update',
                }
            )
            print("After cartitem_group send")

            print("Before addprices_group send")
            async_to_sync(channel_layer.group_send)(
                'addprices_group',
                {
                     'type': 'addprices_update',
                }
             )
            print("After addprices_group send")
            return JsonResponse({'success': True})
        print("Error in updating.")
        return JsonResponse({'success': False, 'error': 'Error in updating'})
    except Exception as e:
        print("Error in updatedelivery_type:", str(e))
        return JsonResponse({'success': False, 'error': str(e)})
    
@require_http_methods(['GET'])
@user_required
@csrf_protect
def usergetresturant(request):
    if request.method=='GET':
        try:
            restaurants = Restaurant.objects.all() 
            restaurant_data = [
                {
                    'resturant_id': restaurant.email,
                    'resturant_name': restaurant.restaurant_name,
                    'resturant_image': restaurant.restaurant_image.url if restaurant.restaurant_image else None, 
                    'description':restaurant.restaurant_description,
                }
                for restaurant in restaurants
            ]
            return JsonResponse({'success': True, 'data': restaurant_data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@require_http_methods(['GET'])
@user_required
@csrf_exempt
def usertopsellingitems(request):
    if request.method == 'GET':
       try:
            top_selling_items = (
                OrderItem.objects
                .values('item')
                .annotate(total_quantity=Sum('quantity'), total_revenue=Sum('total_price'))
                .order_by('-total_quantity')[:10]
            )
            item_ids = [item['item'] for item in top_selling_items]
            num_top_items = len(item_ids)
            items = Item.objects.select_related('menu', 'submenu','resturant').filter(id__in=item_ids)

            if num_top_items < 10:
                remaining_items_count = 10 - num_top_items
                non_top_selling_items = Item.objects.select_related('menu', 'submenu','resturant').exclude(id__in=item_ids).order_by('-is_available','?')[:remaining_items_count]
                items = list(items) + list(non_top_selling_items)

            elif num_top_items == 10:
                all_items = Item.objects.all()
                if all_items.count() > 10:
                     non_top_selling_items = Item.objects.exclude(id__in=item_ids).order_by('-is_available', '?')[:6]
                     items =  list(items) + list(non_top_selling_items)
            
            cart_items = Cart.objects.filter(user=request.user)
            cart_dict = {cart_item.item_id: cart_item.quantity for cart_item in cart_items}
            data = []
            for item in items:
                 data.append({
                    'item_id': item.id,
                    'item_name': item.item_name,
                    'menu': item.menu.menu_name if item.menu else None,
                    'submenu': item.submenu.sub_menu_name if item.submenu else None,
                    'description': item.description,
                    'type': item.type,
                    'price': float(item.price),
                    'is_available': item.is_available,
                    'preparation_time': item.preparation_time,
                    'item_image': item.item_image.url if item.item_image else None,
                    'in_cart': item.id in cart_dict,
                    'quantity': cart_dict.get(item.id, 0),
                    'resturant_name':item.resturant.restaurant_name,
                })
            return JsonResponse({'success': True, 'data': data})
       except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

#delivery

@delivery_app_required
def deliverygetneworders(request):
    if request.method == 'GET':
        user = request.user
        orders = Order.objects.filter(status='shipped',delivery_person=user,delivery_type='delivery').select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0 
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price  

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None 
                })

            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address':order.delivery_address,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price),  
                'total_item_price': str(item_total_price), 
                'total_additional_charges': str(total_additional_charges), 
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_amount': str(order.payment.amount),
                'payment_status': order.payment.get_status_display(),
                'items': order_items, 
                'additional_charges': additional_charges_data,
                'daily_sequence':order.daily_sequence,  
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@delivery_app_required
@require_POST
@csrf_protect
def deliveryupdatetoshipped(request):
    if request.method == 'POST':
        data=json.loads(request.body)
        order_id = data.get('order_id')
        if order_id:
            try:
                order = Order.objects.get(order_id=order_id,delivery_type='delivery')
                if order.status == 'prepared':
                    order.status = 'shipped' 
                    order.save()
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Order is not in prepared state.'}) 
            except Order.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Order not found.'})
        else:
            return JsonResponse({'success': False, 'error': 'Order ID is missing.'}) 

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def decrypt_order_id(encrypted_order_id):
    part_length = len(encrypted_order_id) // 4
    parts = []
    for i in range(4):
        parts.append(encrypted_order_id[i * part_length: (i + 1) * part_length])
    parts[0], parts[2] = parts[2], parts[0]
    swapped_order_id = "".join(parts)

    new_part_length = len(swapped_order_id) // 5
    new_parts = []
    for i in range(5):
        new_parts.append(swapped_order_id[i * new_part_length: (i + 1) * new_part_length])
    new_parts[0], new_parts[2] = new_parts[2], new_parts[0]
    new_parts[1], new_parts[4] = new_parts[4], new_parts[1]
    
    return "".join(new_parts)

@delivery_app_required
@require_POST
@csrf_protect
def deliveryupdatedeliverystatus(request):
    if request.method == 'POST':
        try:
            try:
                data = json.loads(request.body)
                order_id = data.get('order_id')
                status = data.get('status')
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON format in request body'}, status=400)
            order = Order.objects.get(order_id=order_id)
            
            status_map = {
                "Ordered": "pending",
                "Confirmed": "confirmed",
                "Prepared": "prepared",
                "Shipped": "shipped",
                "Delivered": "delivered",
                "Preparing":"preparing",
                "Ready to Take": "ready_to_take",
                "Received by Customer": "delivered",
                "Served":"delivered",
                "Cancelled":"cancelled",
                "Served to Customer":"delivered",
            }
            if status in status_map:
                status = status_map[status]
            else:
                return JsonResponse({'success': False, 'error': 'Invalid status label received.'}, status=400)

            all_status_choices = [val for val, label in dict(Order.DELIVERY_STATUS_CHOICES + Order.PICKUP_STATUS_CHOICES + Order.DINING_STATUS_CHOICES).items() ]
            if status not in all_status_choices:
               return JsonResponse({'success': False, 'error': 'Invalid status value.'}, status=400)

            current_status_index = get_status_index(order.delivery_type, order.status)
            new_status_index=get_status_index(order.delivery_type, status)

            if new_status_index <= current_status_index and order.status != 'cancelled':
                return JsonResponse({'success': False, 'error': 'Cannot revert back to a previous status'}, status=400)


            order.status = status
            order.delivered_at = timezone.now()
            order.save()
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'delivery_group',
                {
                    "type": 'delivery_delivered_order'
                }
            )
            async_to_sync(channel_layer.group_send)(
                'delivery_group',
                {
                    "type": 'delivery_new_order'
                }
            )
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'admin_group',
                {
                    "type": 'admin_all_order'
                }
            )
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'admin_group',
                {
                    "type": 'admin_delivered_order'
                }
            ) 
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'restaurant_group',
                {
                    "type": 'restaurant_all_order'
                }
            ) 
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'restaurant_group',
                {
                    "type": 'restaurant_delivered_order'
                }
            ) 
            try:
               
                user = order.user
                message,emoji = choice(USER_NOTIFICATION_MESSAGES.get(status,'no notification'))
                notification_message=f"{message} Order ID: {order.order_id} {emoji}"
                user_notification = UserNotification.objects.create(
                    user=user,
                    title='Order Status Updated',
                    message=notification_message,
                    related_order=order
                )
                print('sending notification')
                notification_data = {
                    'user_ids': user.email,
                    'title': 'Order Update',
                    'body': notification_message,
                 }
                notification_response = send_notification_helper(notification_data)
                if notification_response.status_code != 200:
                     print(f"Error sending notification: {notification_response.content}")

            except Exception as e:
                print(f"Error sending notification: {e}")
            
            return JsonResponse({'success': True, 'order_id': order.order_id,'daily_sequence':order.daily_sequence})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'An unexpected error occurred: {e}'})
        
@delivery_app_required
@require_http_methods(['GET'])
@csrf_protect
def get_delivery_performance_chart_data(request):
    user = request.user
    if user:
        try:
            personnel = DeliveryPerson.objects.get(email=user.email)
            today = timezone.now().date()

            last_7_days_data = []
            for i in range(7):
                date = today - timedelta(days=i)
                delivered_orders = Order.objects.filter(
                    delivery_person=personnel,
                    created_at__date=date,
                    status='delivered'
                ).count()
                last_7_days_data.append({'date': date.strftime('%Y-%m-%d'), 'count': delivered_orders})

            last_5_weeks_data = []
            for i in range(5):
                start_date = today - timedelta(weeks=i+1)
                end_date = today - timedelta(weeks=i)
                delivered_orders = Order.objects.filter(
                    delivery_person=personnel,
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date,
                    status='delivered'
                ).count()
                last_5_weeks_data.append({'week': start_date.strftime('%Y-%m-%d'), 'count': delivered_orders})

            last_12_months_data = []
            for i in range(12):
                year = today.year - i
                if i == 0:
                    month = today.month
                else:
                    month = 12
                start_date = timezone.datetime(year, month, 1)
                end_date = timezone.datetime(year, month, 1) + timedelta(days=31)
                delivered_orders = Order.objects.filter(
                    delivery_person=personnel,
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date,
                    status='delivered'
                ).count()
                last_12_months_data.append({'month': start_date.strftime('%Y-%m'), 'count': delivered_orders})

            context = {
                'last_7_days_data': list(reversed(last_7_days_data)),
                'last_5_weeks_data': list(reversed(last_5_weeks_data)),
                'last_12_months_data': list(reversed(last_12_months_data))
            }

            return JsonResponse({'success': True, 'context': context})

        except DeliveryPerson.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Delivery Personnel not found.'}, status=404)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success':False,'error':'Required missing fields.'})
    


@require_http_methods(['GET'])
@delivery_app_required
@csrf_protect
def deliverydeliveredorders(request):
    if request.method == 'GET':
        user = request.user
        orders = Order.objects.filter(status='delivered',delivery_person=user).select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0  
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price 

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None 
                })
            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address':order.delivery_address,
                'delivery_person': order.delivery_person.first_name if order.delivery_person else None,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price), 
                'total_item_price': str(item_total_price),  
                'total_additional_charges': str(total_additional_charges),  
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'delivered_at':timezone.localtime(order.delivered_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_amount': str(order.payment.amount),
                'payment_status': order.payment.get_status_display(), 
                'items': order_items,
                'additional_charges': additional_charges_data,
                'restaurant_name':order.restaurant.restaurant_name,
                'daily_sequence':order.daily_sequence,  
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@require_http_methods(['GET'])
@delivery_app_required
@csrf_protect
def deliverygetorderdetails(request,order_id):
    if request.method == 'GET':
        delivery_person=CustomUser.objects.get(email=request.user.email)
        orders = Order.objects.filter(order_id=order_id,delivery_person=delivery_person).select_related('user', 'payment').prefetch_related('items', 'additional_charges')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0  
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price 

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'description':item.description,
                    'item_image': item.item_image.url if item.item_image else None 
                })
            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'delivery_address':order.delivery_address,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price), 
                'total_item_price': str(item_total_price),  
                'total_additional_charges': str(total_additional_charges),  
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data,
                'restaurant_name':order.restaurant.restaurant_name,
                'daily_sequence':order.daily_sequence,    
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)


#deliveryapp

def deliveryapplogin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = DeliveryPerson.objects.get(email=email) 
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                if user.has_perm('canteenapp.is_deliveryperson'):
                    login(request, user)
                    return redirect('deliveryapphome')
                else:
                   return render(request, 'deliveryapplogin.html', {'error_message': 'Invalid user role.'})
            else:
                 return render(request, 'deliveryapplogin.html', {'error_message': 'Invalid credentials.'})
        except DeliveryPerson.DoesNotExist:
            return render(request, 'deliveryapplogin.html', {'error_message': 'User does not exist.'})
    return render(request, 'deliveryapplogin.html')

@delivery_app_required
def deliveryapphome(request):
    return render(request,'deliveryapphome.html')

@delivery_app_required
def deliveryappscan(request):
    return render(request,'deliveryappscan.html')

@delivery_app_required
def deliveryappnotifications(request):
    return render(request,'deliveryappnotifications.html')

@delivery_app_required
def deliveryappdelivered(request):
    return render(request,'deliveryappdelivered.html')

@delivery_app_required
def deliveryappinsights(request):
    return render(request,'deliveryappinsights.html')

@delivery_app_required
def deliveryappprofile(request):
    return render(request,'deliveryappprofile.html')

@delivery_app_required
def deliveryapplogout(request):
    logout(request)
    return redirect('deliveryapplogin')










#app
def applogin(request):
    return render(request,'applogin.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@app_user_required
def apphome(request):
    return render(request,'apphome.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@app_user_required
def appsearch(request):
    return render(request,'appsearch.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@app_user_required
def appcheckout(request):
    return render(request,'appcheckout.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@app_user_required
def appprofile(request):
    return render(request,'appprofile.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@app_user_required
def apporderhistory(request):
    return render(request,'apporderhistory.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@app_user_required
def apporderinfo(request):
    return render(request,'apporderinfo.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@app_user_required
def applogout(request):
    logout(request)
    return redirect('applogin')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@app_user_required
def google_auth_redirect(request):
    next_url = request.GET.get('next') 
    if next_url:
        return redirect(next_url)
    else:
        return redirect('/') 

@cache_control(no_cache=True, must_revalidate=True, no_store=True)   
@app_user_required
def appnotifications(request):
    return render(request,'appnotifications.html')
    
def pagenotfound(request):
    return render(request,'pagenotfound.html')

 #resturant

def resturantlogin(request):
    if request.method == 'POST':
        email = request.POST.get('email') 
        password = request.POST.get('password')
        try:
            user = Restaurant.objects.get(email=email)
            user=authenticate(request,username=user.username,password=password)
            if user is not None:
                if user.has_perm('canteenapp.is_restaurant'):
                    login(request, user)
                    return redirect('resturantdashoard')
                else:
                    return render(request, 'resturantlogin.html', {'error_message': 'Invalid user role.'})
            else:
                return render(request, 'resturantlogin.html', {'error_message': 'Invalid username or password.'})
        except Restaurant.DoesNotExist:
            return render(request, 'resturantlogin.html', {'error_message': 'User does not exist.'})

    return render(request, 'resturantlogin.html')

@restaurant_required
@require_http_methods(["GET"])
@csrf_protect
def restaurantgetmenu(request):
    if request.method=='GET':
        try:
            menus = Menu.objects.all()
            menu_list = []
            for menu in menus:
                menu_data = {
                    'menu_id':menu.id,
                    'menu_name':menu.menu_name,
                    'menu_picture': menu.menu_image.url if menu.menu_image else None
                }
                menu_list.append(menu_data)
            
            return JsonResponse({'success': True, 'data': menu_list})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@restaurant_required
@require_http_methods(["POST"])
@csrf_protect
def restaurantgetsubmenusfordropdown(request):
    if request.method == 'POST':
        try:
            data=json.loads(request.body)
            menu_id=data.get('menu_id')
            menu=Menu.objects.get(id=menu_id)
            submenus = SubMenu.objects.filter(menu_name=menu)
            submenu_data = [{'sub_menu_id': submenu.id, 'sub_menu_name': submenu.sub_menu_name} for submenu in submenus]
            return JsonResponse({'success': True, 'data': submenu_data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    
@restaurant_required
@require_POST
@csrf_protect
def restaurantadditem(request):
    if request.method == 'POST':
        try:
            item_name = request.POST.get('itemname')
            description = request.POST.get('description')
            menu_id = request.POST.get('menu')
            submenu_id = request.POST.get('submenu')
            item_type = request.POST.get('type') 
            price = request.POST.get('price')
            is_available = request.POST.get('is_available')
            item_image = request.FILES.get('itemimage')
            preparation_time=request.POST.get('preparation_time')
            restaurant=request.user.email
            if is_available == 'on': 
                is_available = True
            elif is_available is None:
                is_available = False
            if not all([item_name, description, price]):
                return JsonResponse({'success': False, 'error': 'Item name, description, and price are required.'})
            if len(description) < 20:
                return JsonResponse({'success': False, 'error': 'Description must be at least 20 characters long.'})

            menu = Menu.objects.get(pk=menu_id) if menu_id else None
            submenu = SubMenu.objects.get(pk=submenu_id) if submenu_id else None
            restaurant=Restaurant.objects.get(email=restaurant) if restaurant else None

            item = Item.objects.create(
                menu=menu,
                submenu=submenu,
                item_name=item_name,
                description=description,
                type=item_type,  
                price=price,
                is_available=is_available,
                item_image=item_image,
                preparation_time=preparation_time,
                resturant=restaurant
            )
            if item:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'allitems_group',
                    {
                        'type': 'items_update',
                    }
                )
                return JsonResponse({'success': True})
            
        except Menu.DoesNotExist:
            return JsonResponse({'success':False,'error':'Menu not exists.'})
        except SubMenu.DoesNotExist:
            return JsonResponse({'success':False,'error':'Submenu not exists.'})
        except Exception as e:
            return JsonResponse({'success':False,'error':str(e)})

@require_POST  
@restaurant_required
@csrf_protect
def restaurantgetallitems(request):
    if request.method=='POST':
        try:
            restaurant=CustomUser.objects.get(email=request.user.email)
            items = Item.objects.filter(resturant=restaurant)
            item_data = [
                {
                    'item_id': item.id,
                    'item_name':item.item_name,
                    'menu': item.menu.menu_name if item.menu else None, 
                    'submenu': item.submenu.sub_menu_name if item.submenu else None,
                    'description':item.description,
                    'restaurant':item.resturant.restaurant_name if item.resturant else None,
                    'type':item.type,
                    'price':item.price,
                    'is_avialable':item.is_available,
                    'preparation_time':item.preparation_time,
                    'item_image': item.item_image.url if item.item_image else None,
                    'count':item.count,
                }
                for item in items
            ]
            return JsonResponse({'success': True, 'data': item_data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@require_http_methods(["DELETE"])
@restaurant_required
@csrf_protect
def restaurantdeleteitem(request):
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        if not item_id:
            return JsonResponse({'success': False, 'error': 'Item ID is required.'}, status=400)
        item = Item.objects.get(id=item_id)
        if item.item_image:
            try:
                image_path = item.item_image.path 
                if os.path.isfile(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error deleting image: {e}")
        item.delete()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'allitems_group',
            {
                'type': 'items_update',
            }
        )
        async_to_sync(channel_layer.group_send)(
            'cartitem_group',
            {
                'type': 'cart_update',
            }
        )
        return JsonResponse({'success': True})
    except Menu.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@restaurant_required
@require_POST
@csrf_protect
def restaurantupdateitem(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id=data.get('item_id')
            item_name = data.get('item_name')
            description = data.get('description')
            price = data.get('price')
            is_available = data.get('is_avialable')
            item_quantity=data.get('item_quantity')
            if is_available == 'on': 
                is_available = True
            elif is_available is None:
                is_available = False
            preparation_time = data.get('preparation_time')
            if not item_name:
                return JsonResponse({'success': False, 'error': 'Item name cannot be empty.'}, status=400)
            if len(description.split()) < 10: 
                return JsonResponse({'success': False, 'error': 'Description must be at least 20 words long.'}, status=400)

            item=Item.objects.get(id=item_id)
            item.item_name=item_name
            item.preparation_time=preparation_time
            item.description=description
            item.price=price
            item.is_available=is_available
            item.count=int(item_quantity)
            item.save()
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'allitems_group',
                {
                    'type': 'item_update',
                    'item_id': item.id,
                }
            )
            async_to_sync(channel_layer.group_send)(
                'cartitem_group',
                {
                    'type': 'cart_update',
                }
            )
            async_to_sync(channel_layer.group_send)(
                'search_items_group',
                {
                    'type': 'search_update',
                }
            )
            async_to_sync(channel_layer.group_send)(
                'search_items_group',
                {
                    'type': 'search_update',
                    'item_id': item.id,
                }
            )
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@restaurant_required
@require_POST
@csrf_protect
def restaurantupdateitemimage(request):
    if request.method=='POST':
        try:
            item_id = request.POST.get('item_id')
            item = Item.objects.get(pk=item_id)
            itemimage = request.FILES.get('itemimage')
        
            if itemimage:
                if item.item_image: 
                    try:
                        old_image_path = os.path.join(settings.MEDIA_ROOT, str(item.item_image))
                        if os.path.isfile(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        print(f"Error deleting old image: {e}")

                item.item_image = itemimage
                item.save()
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'allitems_group',
                    {
                        'type': 'item_update',
                        'item_id': item.id,
                    }
                )
                async_to_sync(channel_layer.group_send)(
                    'cartitem_group',
                    {
                        'type': 'cart_update',
                    }
                )
                async_to_sync(channel_layer.group_send)(
                    'search_items_group',
                    {
                        'type': 'search_update',
                        'item_id': item.id,
                    }
                )
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'No image provided.'})

        except Item.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Menu not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}) 

@restaurant_required
def resturantdashoard(request):
    return render(request,'resturantdashboard.html')

@restaurant_required
def resturantitems(request):
    return render(request,'resturantitems.html')

@restaurant_required
def restaurantneworders(request):
    return render(request,'restaurantneworders.html')

@require_http_methods(["POST"])
@restaurant_required
@csrf_protect
def restaurantgetneworder(request):
    if request.method == 'POST':
        restaurant=CustomUser.objects.get(email=request.user.email)
        orders = Order.objects.filter(restaurant=restaurant,status='confirmed', customer_status='confirmed').select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0 
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price  

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None 
                })

            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address':order.delivery_address,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price),  
                'total_item_price': str(item_total_price), 
                'total_additional_charges': str(total_additional_charges), 
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items, 
                'additional_charges': additional_charges_data,
                'daily_sequence':order.daily_sequence, 
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@restaurant_required
@require_POST
@csrf_exempt
def restaruntcancelorder(request):
    try:
        data=json.loads(request.body)
        order_id = data.get('order_id')
        cancel_reason =data.get('cancel_reason')
        
        if not all([order_id, cancel_reason]):
            return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)
        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found.'}, status=404)

        if order.status == 'pending':
            order.status = 'cancelled'
            order.cancel_reason = cancel_reason
            order.cancelled_at=timezone.now()
            order.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Order is not in pending state.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@restaurant_required
def restaurantallorders(request):
    return render(request,'restaurantallorders.html')

@require_http_methods(["POST"])
@restaurant_required
@csrf_protect
def restaurantgetallorder(request):
    if request.method == 'POST':
        restaurant=CustomUser.objects.get(email=request.user.email)
        orders = Order.objects.filter(restaurant=restaurant).select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0  
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price 

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None 
                })
            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address':order.delivery_address,
                'delivery_person': order.delivery_person.first_name if order.delivery_person else None,
                'delivered_at': timezone.localtime(order.delivered_at).strftime('%d-%m-%Y %H:%M:%S') if order.delivered_at else None,
                'cancelled_at': timezone.localtime(order.cancelled_at).strftime('%d-%m-%Y %H:%M:%S') if order.cancelled_at else None,
                'cancel_reason':order.cancel_reason,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price), 
                'total_item_price': str(item_total_price),  
                'total_additional_charges': str(total_additional_charges),  
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data,
                'daily_sequence':order.daily_sequence,  
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@restaurant_required
def restaurantdeliveredorders(request):
    return render(request,'restaurantdeliveredorders.html')

@require_http_methods(['POST'])
@restaurant_required
@csrf_protect
def restaurantgetdeliveredorders(request):
    if request.method == 'POST':
        restaurant=CustomUser.objects.get(email=request.user.email)
        orders = Order.objects.filter(restaurant=restaurant,status='delivered',customer_status='confirmed').select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0  
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price 

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None 
                })
            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address':order.delivery_address,
                'delivery_person': order.delivery_person.first_name if order.delivery_person else None,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price), 
                'total_item_price': str(item_total_price),  
                'total_additional_charges': str(total_additional_charges),  
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'delivered_at':timezone.localtime(order.delivered_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data,
                'daily_sequence':order.daily_sequence,  
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@restaurant_required
def restaurantcancelledorders(request):
    return render(request,'restaurantcancelledorders.html')

@require_http_methods(['POST'])
@restaurant_required
@csrf_protect
def restaurantgetcancelledorders(request):
    if request.method == 'POST':
        restaurant=CustomUser.objects.get(email=request.user.email)
        orders = Order.objects.filter(restaurant=restaurant,status='cancelled',customer_status='confirmed').select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0  
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price 

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None 
                })
            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address':order.delivery_address,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price), 
                'total_item_price': str(item_total_price),  
                'total_additional_charges': str(total_additional_charges),  
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'cancelled_at':timezone.localtime(order.cancelled_at).strftime('%d-%m-%Y %H:%M:%S'),
                'cancel_reason':order.cancel_reason,
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data,
                'daily_sequence':order.daily_sequence,  
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@restaurant_required
@csrf_protect
@require_POST
def restaurantupdateorderstatus(request):
    channel_layer=get_channel_layer()
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        status = data.get('status')
    except json.JSONDecodeError:
      return JsonResponse({'success': False, 'error': 'Invalid JSON format in request body'}, status=400)
    if request.method == 'POST':
        try:
            order = Order.objects.get(order_id=order_id)
            
            status_map = {
                "Ordered": "pending",
                "Confirmed": "confirmed",
                "Prepared": "prepared",
                "Shipped": "shipped",
                "Delivered": "delivered",
                "Preparing":"preparing",
                "Ready to Take": "ready_to_take",
                "Received by Customer": "delivered",
                "Served":"delivered",
                "Cancelled":"cancelled",
                "Served to Customer":"delivered",
            }
            if status in status_map:
                status = status_map[status]
            else:
                return JsonResponse({'success': False, 'error': 'Invalid status label received.'}, status=400)

            all_status_choices = [val for val, label in dict(Order.DELIVERY_STATUS_CHOICES + Order.PICKUP_STATUS_CHOICES + Order.DINING_STATUS_CHOICES).items() ]
            if status not in all_status_choices:
               return JsonResponse({'success': False, 'error': 'Invalid status value.'}, status=400)

            current_status_index = get_status_index(order.delivery_type, order.status)
            new_status_index=get_status_index(order.delivery_type, status)

            if new_status_index <= current_status_index and order.status != 'cancelled':
                return JsonResponse({'success': False, 'error': 'Cannot revert back to a previous status'}, status=400)


            order.status = status
            order.save()
            async_to_sync(channel_layer.group_send)(
                    'admin_group',
                    {
                        "type": 'admin_all_order'
                    }
             )
            async_to_sync(channel_layer.group_send)(
                    'restaurant_group',
                    {
                        "type": 'restaurant_all_order'
                    }
            )
            async_to_sync(channel_layer.group_send)(
                'delivery_group',
                {
                    "type": 'delivery_new_order'
                }
            )
            async_to_sync(channel_layer.group_send)(
                'delivery_group',
                {
                   "type": 'delivery_delivered_order'
                }
            )
        
            async_to_sync(channel_layer.group_send)(
                'admin_group',
                {
                    "type": 'admin_delivered_order'
                }
            ) 
            async_to_sync(channel_layer.group_send)(
                'restaurant_group',
                {
                    "type": 'restaurant_new_order'
                }
            ) 
            async_to_sync(channel_layer.group_send)(
                'restaurant_group',
                {
                    "type": 'restaurant_delivered_order'
                }
            )
            async_to_sync(channel_layer.group_send)(
                    'admin_group',
                    {
                        "type": 'admin_new_order'
                    }
            )
            try:
               
                user = order.user
                message,emoji = choice(USER_NOTIFICATION_MESSAGES.get(status,'no notification'))
                notification_message=f"{message} Order ID: {order.order_id} {emoji}"
                user_notification = UserNotification.objects.create(
                    user=user,
                    title='Order Status Updated',
                    message=notification_message,
                    related_order=order
                )
                print('sending notification')
                notification_data = {
                    'user_ids': user.email,
                    'title': 'Order Update',
                    'body': notification_message,
                 }
                notification_response = send_notification_helper(notification_data)
                if notification_response.status_code != 200:
                     print(f"Error sending notification: {notification_response.content}")

            except Exception as e:
                print(f"Error sending notification: {e}")


            return JsonResponse({'success': True})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid order'}, status=404)
        except ValidationError as e:
          return JsonResponse({'success':False, 'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@require_http_methods(['GET'])
@restaurant_required
@csrf_protect
def restaurantgetorderdetails(request,order_id):
    if request.method == 'GET':
        restaurant=CustomUser.objects.get(email=request.user.email)
        orders = Order.objects.filter(order_id=order_id,restaurant=restaurant).select_related('user', 'payment').prefetch_related('items', 'additional_charges')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0  
            for order_item in order.orderitem_set.all(): 
                item = order_item.item
                item_total_price += order_item.total_price 

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),  
                    'type': item.get_type_display(),
                    'description':item.description,
                    'item_image': item.item_image.url if item.item_image else None 
                })
            additional_charges_data = []
            total_additional_charges = 0 
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value  

            order_data.append({
                'order_id': order.order_id,
                'delivery_address':order.delivery_address,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price), 
                'total_item_price': str(item_total_price),  
                'total_additional_charges': str(total_additional_charges),  
                'status': order.get_status_display(),
                'delivery_type': order.delivery_type.capitalize(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data,
                'restaurant_name':order.restaurant.restaurant_name,
                'daily_sequence':order.daily_sequence,    
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@restaurant_required
def restaurantplaceorderpage(request):
    return render(request,'restaurantplaceorder.html')

@restaurant_required
@require_POST
@csrf_protect
def restaurantplaceorder(request):
    if request.method=='POST':
        try:
            data = json.loads(request.body)
            delivery_type= data.get('deliveryType')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return JsonResponse({'success': False, 'error': 'Cart is empty.'}, status=400)
        for cart_item in cart_items:
           if cart_item.quantity > cart_item.item.count:
                return JsonResponse({
                    'success': False,
                    'error': f"Insufficient stock for item {cart_item.item.item_name}. "
                }, status=400)
        base_total = sum(cart_item.item.price for cart_item in cart_items)
        additional_charges = 0
        charges_to_add = ['Packaging','GST','Other','PlatFormFee']
        for charge_type in charges_to_add:
            try:
                price = Prices.objects.get(price_type=charge_type)
                additional_charges += price.calculate_charge(base_total)

            except Prices.DoesNotExist:
                print(f"Warning: Price for {charge_type} not found in database.")
        total_amount = base_total + additional_charges
        order_id=generate_order_id()
        payment=Payment.objects.create(
            user=request.user,
            amount=total_amount,
            order_id=order_id,
            status='success',
            payment_method = 'pay_on_delivery',
            transaction_id=order_id,
        )
        restaurant=Restaurant.objects.get(email=request.user.email)
        order = Order(
            user=request.user,
            payment=payment,
            restaurant=restaurant,
            delivery_type = 'pay_on_delivery',
            status = delivery_type
        )
        order.order_id = payment.order_id  
        order.create_order_from_cart(cart_items,payment.created_at)
        order.save()
        cart_items.delete()
        async_to_sync(channel_layer.group_send)(
            'admin_group',
            {
                "type": 'admin_all_order'
            }
        )
        async_to_sync(channel_layer.group_send)(
            'restaurant_group',
            {
                "type": 'restaurant_all_order'
            }
        )

        
        async_to_sync(channel_layer.group_send)(
            'admin_group',
            {
                "type": 'admin_delivered_order'
            }
        ) 
        async_to_sync(channel_layer.group_send)(
            'restaurant_group',
            {
                "type": 'restaurant_new_order'
            }
        ) 
        async_to_sync(channel_layer.group_send)(
            'restaurant_group',
            {
                "type": 'restaurant_delivered_order'
            }
        )
        async_to_sync(channel_layer.group_send)(
            'admin_group',
            {
                "type": 'admin_new_order'
            }
        )
        async_to_sync(channel_layer.group_send)(
            'cartitem_group',
            {
                'type': 'cart_update',
            }
        )
        async_to_sync(channel_layer.group_send)(
            'allitems_group',
            {
                'type': 'items_update',
            }
        )
        return JsonResponse({'success': True})
    return JsonResponse({'success':False,'error':'Invalid request.'})

@restaurant_required
def restaurantlogout(request):
    logout(request)
    return redirect('resturantlogin')


#restaurantapplogin

def restaurantapplogin(request):
    if request.method == 'POST':
        email = request.POST.get('email') 
        password = request.POST.get('password')
        try:
            user = Restaurant.objects.get(email=email)
            user=authenticate(request,username=user.username,password=password)
            if user is not None:
                if user.has_perm('canteenapp.is_restaurant'):
                    
                    login(request, user)
                    return redirect('restaurantapphome')
                else:
                    return render(request, 'restaurantapplogin.html', {'error_message': 'Invalid user role.'})
            else:
                return render(request, 'restaurantapplogin.html', {'error_message': 'Invalid user role.'})
        except Restaurant.DoesNotExist:
            return render(request, 'restaurantapplogin.html', {'error_message': 'User does not exist.'})

    return render(request, 'restaurantapplogin.html')

@restaurant_app_required
def restaurantapphome(request):
    return render(request,'restaurantapphome.html')

#payment gateway phonepe


logger = logging.getLogger('payment')
logger = logging.getLogger(__name__)
merchant_id = "DEMOUAT"  
salt_key = "2a248f9d-db24-4f2d-8512-61449a31292f"  
salt_index = 1 
env = Env.UAT
should_publish_events = True

# Initialize PhonePe Client
phonepe_client = PhonePePaymentClient(
    merchant_id=merchant_id,
    salt_key=salt_key,
    salt_index=salt_index,
    env=env,
    should_publish_events=should_publish_events
)
def generate_order_id():
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    random_string=''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    order_id = f"{timestamp}{random_string}"
    return order_id

@csrf_exempt
def initiate_payment(request):
    """Handles payment initiation and transaction for PhonePe gateway."""
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method.")

    try:
        #request data from the frontend
        data = json.loads(request.body)
        delivery_address = data.get('delivery_address')
        #validate the data
        if request.user.delivery_type=='delivery':
            if not delivery_address:
                return JsonResponse({'success':False,'error':'Delivery address required'})
        #fetch the user cart items
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return JsonResponse({'success': False, 'error': 'Cart is empty.'}, status=400)
        for cart_item in cart_items:
           if cart_item.quantity > cart_item.item.count:
                return JsonResponse({
                    'success': False,
                    'error': f"Insufficient stock for item {cart_item.item.item_name}. "
                }, status=400)
        #calculate the total prices with additional charges
        base_total = sum(cart_item.item.price for cart_item in cart_items)
        additional_charges = 0
        #check the delivery type
        if request.user.delivery_type == 'delivery':
             charges_to_add = ['Delivery', 'Packaging','GST','Other','PlatFormFee']
        elif request.user.delivery_type == 'dining':
            charges_to_add = ['Service','GST','Other','PlatFormFee']
        elif request.user.delivery_type == 'pickup':
            charges_to_add = ['Packaging','GST','Other','PlatFormFee']
        else:
            charges_to_add = []
        #compute the total charges
        for charge_type in charges_to_add:
            try:
                price = Prices.objects.get(price_type=charge_type)
                additional_charges += price.calculate_charge(base_total)

            except Prices.DoesNotExist:
                print(f"Warning: Price for {charge_type} not found in database.")
        #total_price
        total_amount = base_total + additional_charges
        
        #Generate Unique Transaction ID
        merchant_transaction_id = str(uuid.uuid4())
        #create a payment for the transaction
        amount_in_paise = int(total_amount * 100)
        Payment.objects.create(
            user=request.user,
            amount=total_amount,
            transaction_id=merchant_transaction_id,
            order_id=generate_order_id(),
            status='pending',
        )

        redirect_url = "http://127.0.0.1:8000/apphome/"  # UI Redirect after payment
        callback_url = "https://1df8-2409-40f0-40ce-232f-2c6b-9a3f-bcb6-dff7.ngrok-free.ap/phonepe_callback/"  # S2S Callback

        #Build Payment Request
        pay_request = PgPayRequest.pay_page_pay_request_builder(
            merchant_transaction_id=merchant_transaction_id,
            amount=amount_in_paise,
            merchant_user_id=str(request.user.id), 
            redirect_url=redirect_url,
            callback_url=callback_url
        )

        #Make Payment Request
        pay_response = phonepe_client.pay(pay_request)
        pay_page_url = pay_response.data.instrument_response.redirect_info.url
        #return the payment url
        return JsonResponse({'success': True, 'payment_url': pay_page_url,'merchant_transaction_id': merchant_transaction_id })

    except Exception as e:
        # Handle Errors Gracefully
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def phonepe_callback(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method.")

    try:
        #verify the headers return by the phonepe
        x_verify_header_data = request.headers.get('X-VERIFY')
        if not x_verify_header_data:
            return JsonResponse({'success': False, 'error': 'X-VERIFY header missing.'}, status=400)
        #check valifity for the headers
        is_valid = phonepe_client.verify_response(
            x_verify=request.headers.get('X-VERIFY'), response= request.body
        )
        if not is_valid:
            return JsonResponse({'success': False, 'error': 'Invalid callback signature.'}, status=400)
        #request body from the response
        phonepe_s2s_callback_response_body_string = request.body
        #get the encoded data
        encoded_response = json.loads(phonepe_s2s_callback_response_body_string)['response']
        #decode the encoded reponse
        decoded_response = base64.b64decode(encoded_response)
        #get the json object from decoded reposnse
        response_data = json.loads(decoded_response)
        #get the merchant_transaction_id
        merchant_transaction_id = response_data['data']['merchantTransactionId']
        #check the status of the merchant_transaction_id
        response = phonepe_client.check_status(merchant_transaction_id)
        try:
            if response and response.data:  
                #get the required details from the check_status response
                transaction_id = response.data.transaction_id
                amount = response.data.amount / 100 
                response_code = response.data.response_code
                state = response.data.state
                payment_instrument = response.data.payment_instrument   

                #check the payment_type
                if payment_instrument:
                    payment_instrument_type = payment_instrument.type.value  
                    if payment_instrument_type == "CARD":
                        pg_transaction_id = payment_instrument.pg_transaction_id
                        pg_authorization_code = payment_instrument.pg_authorization_code
                        bank_id = payment_instrument.bank_id
                        print(f"PG Transaction ID: {pg_transaction_id}")
                        print(f"PG Authorization Code: {pg_authorization_code}")
                    elif payment_instrument_type == "UPI":
                        ifsc = payment_instrument.ifsc
                        utr = payment_instrument.utr
                        print(f"IFSC: {ifsc}")
                        print(f"UTR: {utr}")
                    elif payment_instrument_type == "NETBANKING":
                        bank_id = payment_instrument.bank_id
                        bank_transaction_id = payment_instrument.bank_transaction_id
                        print(f"Bank ID: {bank_id}")
                        print(f"Bank Transaction ID: {bank_transaction_id}")
                else:
                    print("No payment instrument found.")
            else:
                return JsonResponse({'success': False, 'error': 'No data found in response.'}, status=400)

            try:
                #filter the payment the payment details using merchant_transaction_id
                payment = Payment.objects.get(transaction_id=merchant_transaction_id)
            except Payment.DoesNotExist:
                print(str(e))
                return JsonResponse({'success': False, 'error': 'Payment not found.'}, status=404)
            #check the state of the payment
            if state != "COMPLETED" or int(payment.amount) != int(amount):
                print(state, int(amount), int(payment.amount))
                if state == "PENDING":
                    payment.status = 'pending'
                    payment.save()
                    return redirect('apphome/') 
                payment.status = 'failed'
                payment.save()
                return redirect('apphome/')
            payment.response_code=response_code
            payment.message=response.message
            payment.status = 'success'
            payment.phonepe_transaction_id = transaction_id
            payment.payment_date=timezone.now()
            payment.payment_method=payment_instrument_type
            payment.save()
            user = payment.user
            delivery_address = None
            if user.delivery_type == 'delivery': 
                delivery_address = user.delivery_address
            #place the order
            cart_items = Cart.objects.filter(user=user)
            restaurant=Restaurant.objects.get(email=cart_items[0].item.resturant.email)
            order = Order(
                user=user,
                delivery_address=delivery_address,
                payment=payment,
                restaurant=restaurant,  
            )

            order.order_id = payment.order_id  
            order.create_order_from_cart(cart_items,payment.created_at)
            order.save()
            cart_items.delete()

            user_message,user_emoji = choice(USER_MESSAGES)
            user_notification_message=f"{user_message} Order ID: {order.order_id} {user_emoji}"
            user_notification=UserNotification.objects.create(
                user=user,
                notification_type='order',
                title='Order Placed',
                message=user_notification_message,
                related_order=order,
            )
            print(user_notification)
            # Restaurant Notification
            restaurant_message, restaurant_emoji = choice(RESTAURANT_MESSAGES)
            restaurant_notification_message=f"{restaurant_message} Order ID: {order.order_id} {restaurant_emoji}"
            restaurant_notification = RestaurantNotification.objects.create(
                user=restaurant,
                notification_type='order',
                title='New Order',
                message=restaurant_notification_message,
                related_order=order,
            )
            print(restaurant_notification)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'admin_group',
                {
                    "type": 'admin_all_order'
                }
            )
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'admin_group',
                {
                    "type": 'admin_new_order'
                }
            ) 
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'restaurant_group',
                {
                    "type": 'restaurant_all_order'
                }
            ) 
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'restaurant_group',
                {
                    "type": 'restaurant_new_order'
                }
            )
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'restaurant_notification_group',
                {
                    "type": 'send_notification_update'
                }
            ) 
            try:
                print('sending notification')
                notification_data = {
                    'user_ids': payment.user.email, 
                    'title': 'Order Placed',
                    'body': user_notification_message,
                }
                
                notification_response = send_notification_helper(notification_data)
                if notification_response.status_code != 200:
                    print(f"Error sending notification: {notification_response.content}")
            except Exception as e:
                print(f"Error sending notification: {e}") 
            return redirect('apphome/')
        except Exception as e:
            print(str(e))
    except Exception as e:
        print(str(e))
        return redirect('apphome/')

def send_notification_helper(data):
    """Helper function to send notifications.  Returns the response object."""
    print('NOTIFICATION HELper')
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post('http://127.0.0.1:8000/sendnotification/', data=json.dumps(data), headers=headers) 
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request error sending notification: {e}")
        return None
    

USER_MESSAGES = [
    ("Your order is confirmed!","🎉"),
    ("We've received your order, and it's being prepared!", "🚀"),
    ("Order successfully placed!", "🥳"),
    ("Your order is on its way!", "👍"),
    ("You're all set, order has been placed","✅")
]

ADMIN_MESSAGES = [
    ("New order received!", "🔔"),
     ("A new sale just came in!", "💰"),
    ("New order from user. check details now!","🧾"),
    ("A new order has been placed!","📈"),
    ("Attention! A new order is ready for processing","📢")

]

RESTAURANT_MESSAGES = [
    ("New order to prepare!", "👨‍🍳"),
    ("Get ready to cook a new order", "🔥"),
    ("You have a new order from client!", "🍜"),
    ("A new order has come in, let's cook!","🧑‍🍳"),
    ("New order, check order details now!","🔔")
]

#payment gateway payu
"""
def get_payu_client():
    return payu_sdk.payUClient({
        "key": settings.PAYU_MERCHANT_KEY,
        "salt": settings.PAYU_MERCHANT_SALT,
        "env": settings.PAYU_ENVIRONMENT
    })

def checkout_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        return render(request, 'checkout.html', {'error': 'Your cart is empty.'})

    if request.method == 'POST':
        try:
            data=json.loads(request.body)
            delivery_address = data.get('delivery_address')
            print(delivery_address)
            if not delivery_address:
                return render(request, 'checkout.html', {'error': 'Please enter your delivery address'})
           
            order = Order(user=request.user, delivery_type=request.user.delivery_type, delivery_address=delivery_address)
            order.create_order_from_cart(cart_items)
            order.save()
            amount = order.total_price
            productinfo = f"Order #{order.order_id}"
            txnid = order.order_id
            hash_string = f"{settings.PAYU_MERCHANT_KEY}|{txnid}|{amount}|{productinfo}|{request.user.first_name}|{request.user.email}|||||||||||{settings.PAYU_MERCHANT_SALT}"
            hash_value = hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()

            payu_url = "https://test.payu.in/_payment"
            payload = {
                "key": settings.PAYU_MERCHANT_KEY,
                "txnid": txnid,
                "amount": amount,
                "productinfo": productinfo,
                "firstname": request.user.first_name,
                "email": request.user.email,
                "phone": request.user.phone_number,
                "surl": request.build_absolute_uri('/payments/payment-success/'),
                "furl": request.build_absolute_uri('/payments/payment-failure/'),
                "hash": hash_value,
            }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = requests.post(payu_url, data=payload, headers=headers)
            print("Response Content:", response.text)
            print("Response Status Code:", response.status_code)

            if response.status_code == 200:
               
                return redirect(response.url) 
            else:
                return JsonResponse({"success": False, "error": "Failed to initiate payment."}, status=500)
        except Exception as e:
            print(str(e))
            return render(request, 'checkout.html', {'error': str(e)})
        

    context = {
        'cart_items': cart_items,
    }
    return render(request, 'checkout.html', context)

@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        response_data = request.POST.dict() # Access POST data as a dictionary
        try:
            transaction_id = response_data['txnid']  # Ensure txnid is received correctly
            order = Order.objects.get(order_id=int(transaction_id))

            # Verification is crucial. Verify the payment with PayU:
            verification_response = verify_payment(transaction_id)
            if verification_response and verification_response['status'] == 1: # Assuming '1' denotes success from verification
                payment, created = Payment.objects.update_or_create(
                    transaction_id=transaction_id,
                    defaults={
                        'user': order.user,
                        'amount': Decimal(response_data['amount']),
                        'status': 'SUCCESS',  # Based on PayU verification
                        'order_id': int(transaction_id), # Convert to integer
                        'payment_method': 'payu',  
                        'message': json.dumps(response_data), # Store full response data
                        'payment_instrument': '' # PayU doesn't have this field in the callback. Adjust if needed.
                    },
                ) 
                order.payment = payment 
                order.customer_status = 'confirmed'
                order.save()

                return render(request, "payment_success.html", {"response": response_data}) # Response Data in the context


            else:
                # Payment verification failed
                order.customer_status = 'cancelled'
                order.save()
                return render(request, "payment_failure.html", {"response": response_data, "error": "Payment verification failed"}) # Include error message in context

        except (Order.DoesNotExist, KeyError, ValueError) as e:  # Handle potential errors
            return render(request, "payment_failure.html", {"response": response_data, "error": str(e)})



    return HttpResponseBadRequest("Invalid request method.")  # Only handle POST


@csrf_exempt
def payment_failure(request):
    if request.method == "POST":
        response_data = request.POST.dict()
        try:
             transaction_id = response_data['txnid']  # Ensure txnid is received correctly
             order = Order.objects.get(order_id=int(transaction_id))
             order.customer_status = 'cancelled'
             order.save()
        except Order.DoesNotExist as e:
            print(str(e))  # Log the error for debugging
            # Handle the case where the order doesn't exist gracefully (e.g., redirect to a generic error page)


        return render(request, "payment_failure.html", {"response": response_data})


    return HttpResponseBadRequest("Invalid request method.")

def verify_payment(transaction_id):
    try:
         response = payu_client.verify_payment({
            "var1": transaction_id
        })
         if response and response.get("status") == 1:
              return response
         else:
            return {"status": 0}
    except Exception as e:  # Handle potential exceptions during verification
        print(f"Error verifying payment: {e}")
        return None  # Or return a specific error value
"""

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def save_fcm_token(request):
    """Saves or updates the FCM device registration token for a user."""

    User = get_user_model()
    try:
        data = request.data 
        print("Received data:", data)

        token = data.get('token')
        user_id = data.get('userId')  

        if not token or not user_id:
            return Response({'error': 'Both token and userId are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=user_id) 
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Error finding user: {e}'}, status=status.HTTP_400_BAD_REQUEST)


        try:
            device_token, created = UserDeviceToken.objects.update_or_create(
                user=user, 
                defaults={'device_registration_token': token}
            )
            message = 'FCM token created successfully.' if created else 'FCM token updated successfully.'
            return Response({'message': message}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        except Exception as e:
            print(f"Error saving token: {e}")
            return Response({'error': f"Error saving token: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:  
        print(f"Unexpected error: {e}") 
        return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_user_id(request):
  try:
     user = request.user
     if not user:
      return Response({'error':'user not found'}, status=status.HTTP_404_NOT_FOUND)
     return Response({'success':True, 'id':user.id}, status=status.HTTP_200_OK)
  except Exception as e:
     return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  
cred_path = "foodhub-c60e4-firebase-adminsdk-oxz22-3e6b763fd3.json" 
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Firebase: {str(e)}")

@csrf_exempt
def send_notification(request):
    """
    Sends a push notification to a list of users based on the provided user IDs and message.
    """
    print('PUSHING NOTIFICATION')
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        user_email = data.get('user_ids')  
        title = data.get('title', '').strip()
        body = data.get('body', '').strip()
        if not user_email or not title or not body:
            
            return JsonResponse({"error": "Missing required fields"}, status=400)

        try:
            user = CustomUser.objects.get(email=user_email)
        except CustomUser.DoesNotExist:
            print(str(e))
            return JsonResponse({"error": "User not found"}, status=404)
        registration_tokens = UserDeviceToken.objects.get(user=user)

        if not registration_tokens:
            return JsonResponse({"error": "No registration tokens found for the user"}, status=404)
        print(registration_tokens)
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=registration_tokens.device_registration_token
        )
        response = messaging.send(message)
        print("Successfully sent message:", response) 
        return JsonResponse({
            'message_id': response  
        })

    except json.JSONDecodeError:
        print(str(e))
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)
    
#notifications

@require_http_methods(['GET'])
@admin_required
def admingetnotifications(request):
    if request.method=='GET':
        notifications = AdminNotification.objects.filter(
            delete_after__gt=timezone.now()
        ).order_by('-created_at')
        notification_list = []
        for notification in notifications:
            notification_list.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'created_at': notification.created_at.isoformat(), 
                'notification_type': notification.notification_type,
                'related_order': notification.related_order.order_id,
            })
        return JsonResponse({'success': True, 'notifications': notification_list})
    return JsonResponse({'success':False,'error':'Invalid request method.'})
    
@require_POST
@restaurant_required
def restaurant_notifications(request):
    if request.method=='POST':
        user_email=request.user.email
        if not user_email:
            return JsonResponse({'success': False, 'error': 'Required user'})
        user = get_object_or_404(CustomUser, email=user_email)
        notifications = RestaurantNotification.objects.filter(
            user=user,
            delete_after__gt=timezone.now()
        ).order_by('-created_at')
        notification_list = []
        for notification in notifications:
            notification_list.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'created_at': notification.created_at.isoformat(), 
                'notification_type': notification.notification_type,
                'related_order': notification.related_order.order_id,
            })
        return JsonResponse({'success': True, 'notifications': notification_list})
    return JsonResponse({'success':False,'error':'Invalid request method.'})
    
@require_POST
@delivery_app_required
def deliverynotifications(request):
    if request.method=='POST':
        user_email=request.user.email
        if not user_email:
            return JsonResponse({'success': False, 'error': 'Required user'})
        user = get_object_or_404(CustomUser, email=user_email)
        notifications = DeliveryPersonNotification.objects.filter(
            user=user,
            delete_after__gt=timezone.now()
        ).order_by('-created_at')
        notification_list = []
        for notification in notifications:
            notification_list.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'created_at': notification.created_at.isoformat(), 
                'notification_type': notification.notification_type,
                'related_order': notification.related_order.order_id,
            })
        return JsonResponse({'success': True, 'notifications': notification_list})
    return JsonResponse({'success':False,'error':'Invalid request method.'})
    
@require_POST
@user_required
def usernotifications(request):
    if request.method == 'POST':
        user_email = request.user.email
        if not user_email:
            return JsonResponse({'success': False, 'error': 'Required user'})
        user = get_object_or_404(CustomUser, email=user_email)

        notifications = UserNotification.objects.filter(
            user=user,
            delete_after__gt=timezone.now()
        ).order_by('-created_at')
        notification_list = []
        for notification in notifications:
            notification_list.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'created_at': notification.created_at.isoformat(), 
                'notification_type': notification.notification_type,
                'related_order': notification.related_order.order_id,
            })
        return JsonResponse({'success': True, 'notifications': notification_list})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})