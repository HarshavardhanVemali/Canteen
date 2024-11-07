from django.shortcuts import render,redirect
from .models import FailedLoginAttempts,RegularUser,DeliveryPerson,Menu,SubMenu,Item,Cart,Prices,Order,OrderItem,Payment,DeliveryLocation,CustomUser
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
from django.contrib.auth.hashers import make_password,check_password
from django.views.decorators.http import require_http_methods
import os
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

def admin_required(view_func):
    return user_passes_test(
        lambda u: u.is_superuser, 
        login_url='/adminlogin/'
    )(view_func)

def deliveryperson_required(view_func):
    return user_passes_test(
        lambda u: u.has_perm('canteenapp.is_deliveryperson') and not u.is_superuser,
        login_url='/deliverylogin/'
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
#admin

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
        hashed_password = make_password(email)
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
            password= hashed_password,
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

            item = Item.objects.create(
                menu=menu,
                submenu=submenu,
                item_name=item_name,
                description=description,
                type=item_type,  
                price=price,
                is_available=is_available,
                item_image=item_image,
                preparation_time=preparation_time
            )
            if item:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'allitems_group',
                    {
                        'type': 'item_update',
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
                    'type':item.type,
                    'price':item.price,
                    'is_avialable':item.is_available,
                    'preparation_time':item.preparation_time,
                    'item_image': item.item_image.url if item.item_image else None
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
                'type': 'item_update',
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
        try:
            data = json.loads(request.body)
            item_id=data.get('item_id')
            item_name = data.get('item_name')
            description = data.get('description')
            price = data.get('price')
            is_available = data.get('is_avialable')
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
            item.save()
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'allitems_group',
                {
                    'type': 'item_update',
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
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@admin_required
@require_POST
@csrf_protect
def adminupdateitemimage(request):
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
                    }
                )
                async_to_sync(channel_layer.group_send)(
                    'cartitem_group',
                    {
                        'type': 'cart_update',
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
        orders = Order.objects.filter(status='pending', customer_status='confirmed').select_related('user', 'payment').prefetch_related('items', 'additional_charges')
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
                'payment_method': order.payment.get_payment_method_display(),
                'payment_amount': str(order.payment.amount),
                'transaction_id': order.payment.transaction_id,
                'payment_status': order.payment.get_status_display(),
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S'),
                'items': order_items, 
                'additional_charges': additional_charges_data  
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
        orders = Order.objects.filter().select_related('user', 'payment').prefetch_related('items', 'additional_charges')
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
                'payment_method': order.payment.get_payment_method_display(),
                'payment_amount': str(order.payment.amount),
                'transaction_id': order.payment.transaction_id,
                'payment_status': order.payment.get_status_display(),
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S'), 
                'items': order_items,
                'additional_charges': additional_charges_data  
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
        orders = Order.objects.filter(status='delivered',customer_status='confirmed').select_related('user', 'payment').prefetch_related('items', 'additional_charges')
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
                'payment_method': order.payment.get_payment_method_display(),
                'payment_amount': str(order.payment.amount),
                'transaction_id': order.payment.transaction_id,
                'payment_status': order.payment.get_status_display(),
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S'), 
                'items': order_items,
                'additional_charges': additional_charges_data  
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
        orders = Order.objects.filter(status='cancelled',customer_status='confirmed').select_related('user', 'payment').prefetch_related('items', 'additional_charges')
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
                'payment_method': order.payment.get_payment_method_display(),
                'payment_amount': str(order.payment.amount),
                'transaction_id': order.payment.transaction_id,
                'payment_status': order.payment.get_status_display(),
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S'), 
                'items': order_items,
                'additional_charges': additional_charges_data  
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
        users = CustomUser.objects.filter(role='user').values('email', 'phone_number', 'role', 'first_name', 'last_name')
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
        orders = Order.objects.filter(status='prepared',delivery_type='delivery',customer_status='confirmed').select_related('user', 'payment').prefetch_related('items', 'additional_charges')
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
                'payment_method': order.payment.get_payment_method_display(),
                'payment_amount': str(order.payment.amount),
                'transaction_id': order.payment.transaction_id,
                'payment_status': order.payment.get_status_display(),
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S'), 
                'items': order_items,
                'additional_charges': additional_charges_data  
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
    data=json.loads(request.body)
    order_id=data.get('order_id')
    delivery_personnel=data.get('delivery_personnel')
    if not all([order_id,delivery_personnel]):
        return JsonResponse({'success':False,'error':'Required missing fields.'})
    try:
        delivery_personnel=DeliveryPerson.objects.get(email=delivery_personnel)
    except DeliveryPerson.DoesNotExist:
        return JsonResponse({'success':False,'error':'Delivery Personnel not exists.'})
    try:
        order=Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({'success':False,'error':'Order not exists.'})
    try:
        order.delivery_person=delivery_personnel
        order.status='shipped'
        order.save()
        return JsonResponse({'success':True})
    except Exception as e:
        return JsonResponse({'success':False,'error':str(e)})

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
        orders = Order.objects.filter(user=user).select_related('user', 'payment').prefetch_related('items')
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
                'payment_method': order.payment.get_payment_method_display(),
                'payment_amount': str(order.payment.amount),
                'transaction_id': order.payment.transaction_id,
                'payment_status': order.payment.get_status_display(),
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S'), 
                'items': order_items,
                'additional_charges': additional_charges_data  
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
                        username=username,
                        first_name=username,
                        email=email,
                        phone_number=phone_number,
                        role='user'
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
@csrf_protect
def getmenu(request):
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
    
@require_http_methods(["GET"])
@user_required
@csrf_protect
def getallitems(request):
    try:
        items = Item.objects.select_related('menu', 'submenu').all()
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
                'quantity': cart_dict.get(item.id, 0)
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
                'quantity': cart_dict.get(item.id, 0)
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

@user_required
@require_POST
@csrf_protect
def add_to_cart(request):
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
                    'allitems_group',
                    {
                        'type': 'item_update',
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
                
                return JsonResponse({'success':True})
            except Item.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Item does not exist.'})    
        if operation == 'increment':
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
                return JsonResponse({'success': True, 'removed': True, 'message': 'Item removed from cart'})
        if cart_item.pk:
            cart_item.save()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
             'allitems_group',
            {
                'type': 'item_update',
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
        return JsonResponse({'success': True, 'quantity': cart_item.quantity, 'total_price': cart_item.item.price * cart_item.quantity})

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
        orders = Order.objects.filter(user=user).select_related('user', 'payment').prefetch_related('items')
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
                'payment_method': order.payment.get_payment_method_display(),
                'payment_amount': str(order.payment.amount),
                'transaction_id': order.payment.transaction_id,
                'payment_status': order.payment.get_status_display(),
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S'), 
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
    query = request.GET.get('q', '')
    if query:
        items = Item.objects.filter(
            Q(item_name__icontains=query) | 
            Q(menu__menu_name__icontains=query) | 
            Q(submenu__sub_menu_name__icontains=query)
        ).select_related('menu', 'submenu')

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
                'quantity': cart_dict.get(item.id, 0)
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

#delivery
def deliverylogin(request):
    if request.method == 'POST':
        email = request.POST.get('email') 
        password = request.POST.get('password')
        print(email,password)
        try:
            user = CustomUser.objects.get(email=email)
            if user is not None:
                if user.has_perm('canteenapp.is_deliveryperson'):
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                    return redirect('deliverydashboard')
                else:
                    return render(request, 'deliverylogin.html', {'error_message': 'Invalid user role.'})
            else:
                return render(request, 'deliverylogin.html', {'error_message': 'Invalid user role.'})
        except CustomUser.DoesNotExist:
            return render(request, 'deliverylogin.html', {'error_message': 'User does not exist.'})

    return render(request, 'deliverylogin.html')

@deliveryperson_required
def deliverytemplate(request):
    return render(request,'deliverytemplate.html')

@deliveryperson_required
def deliveryneworders(request):
    return render(request,'deliveryneworders.html')

@deliveryperson_required
def deliverydashboard(request):
    return render(request,'deliverydashboard.html')

@deliveryperson_required
def deliverygetneworders(request):
    if request.method == 'GET':
        user = request.user
        orders = Order.objects.filter(status='prepared',delivery_person=user,delivery_type='delivery').select_related('user', 'payment').prefetch_related('items', 'additional_charges')
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
                'additional_charges': additional_charges_data  
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@deliveryperson_required
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

@deliveryperson_required
def deliveryupdatestatus(request):
    return render(request,'deliveryupdatestatus.html')

@deliveryperson_required
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
    
@deliveryperson_required
def deliverydelivered(request):
    return render(request,'deliverydelivered.html')

@require_http_methods(['GET'])
@deliveryperson_required
@csrf_protect
def deliverydeliveredorders(request):
    if request.method == 'GET':
        user = request.user
        orders = Order.objects.filter(status='delivered',delivery_person=user).select_related('user', 'payment').prefetch_related('items', 'additional_charges')
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
                'additional_charges': additional_charges_data  
            })
        
        return JsonResponse({'orders': order_data})

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def applogin(request):
    return render(request,'applogin.html')

def apphome(request):
    return render(request,'apphome.html')

def appsearch(request):
    return render(request,'appsearch.html')

def appcheckout(request):
    return render(request,'appcheckout.html')

def appprofile(request):
    return render(request,'appprofile.html')

def apporderhistory(request):
    return render(request,'apporderhistory.html')

def apporderinfo(request):
    return render(request,'apporderinfo.html')

def applogout(request):
    logout(request)
    return redirect('applogin')

def google_auth_redirect(request):
    next_url = request.GET.get('next') 
    if next_url:
        return redirect(next_url)
    else:
        return redirect('/') 