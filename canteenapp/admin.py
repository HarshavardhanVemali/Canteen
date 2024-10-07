from django.contrib import admin
from .models import CustomUser, DeliveryPerson, RegularUser, Admin,FailedLoginAttempts,EmailVerification

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'role', 'date_joined')
    search_fields = ('email', 'phone_number')
    list_filter = ('is_active', 'role')

class EmailVerificationAdmin(admin.ModelAdmin):
    list_display=('email','verification_code','created_at','expires_at','request_id','is_verified')
    search_fields=('email','verification_code')
    list_filter=('email','verification_code')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(FailedLoginAttempts)
admin.site.register(DeliveryPerson, CustomUserAdmin)
admin.site.register(RegularUser, CustomUserAdmin)
admin.site.register(Admin, CustomUserAdmin)
admin.site.register(EmailVerification,EmailVerificationAdmin)
