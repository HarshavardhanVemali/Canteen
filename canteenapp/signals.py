from django.utils.text import slugify
from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db.models import Q

def create_unique_username(strategy, details, backend, user=None, *args, **kwargs):
    from .models import RegularUser  
    from django.contrib.auth import authenticate, login
    from django.contrib.auth.models import Permission, ContentType
    from django.contrib.auth.decorators import user_passes_test
    from django.shortcuts import render,redirect
    first_name = details.get('first_name', '')
    last_name = details.get('last_name', '')
    email = details.get('email', '')

    print(details)
    if RegularUser.objects.filter(email=email).exists():
        return  

    if first_name and last_name:
        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            base_username = slugify(full_name)
            username = base_username
            counter = 1
            while RegularUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            details['username'] = username
            try:
                user = RegularUser(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    role='user',
                )
                user.save()

                user_permission, created = Permission.objects.get_or_create(
                    codename='is_user',
                    name='Can access user-specific features',
                    content_type=ContentType.objects.get_for_model(RegularUser)
                )
                user.user_permissions.add(user_permission)

            except Exception as e:
                print(f"Error while saving user: {e}")

@receiver(post_save, sender='canteenapp.Item') 
def remove_unavailable_item_from_cart(sender, instance, **kwargs):
    from .models import Cart 
    
    if not instance.is_available:
        Cart.objects.filter(item=instance).delete()