from django.contrib import admin
from .models import CustomUser, DeliveryPerson, RegularUser, Admin,FailedLoginAttempts,EmailVerification,Menu,SubMenu,Item,Cart,Prices,Order,Refund,OrderItem,Payment,OrderAdditionalCharges,DeliveryLocation
from django.utils.safestring import mark_safe

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'role', 'date_joined')
    search_fields = ('email', 'phone_number')
    list_filter = ('is_active', 'role')

class EmailVerificationAdmin(admin.ModelAdmin):
    list_display=('email','verification_code','created_at','expires_at','request_id','is_verified')
    search_fields=('email','verification_code')
    list_filter=('email','verification_code')

class MenuAdmin(admin.ModelAdmin):
    list_display=('id','menu_name','preview_image','schedule_time')
    search_fields=('id','menu_name')
    readonly_fields = ('preview_image',)

    def preview_image(self, obj):
        if obj.menu_image:
            return mark_safe(f'<img src="{obj.menu_image.url}" style="max-width: 200px; max-height: 150px;">')
        else:
            return 'No image found'

class SubMenuAdmin(admin.ModelAdmin):
    list_display=('id','menu_name','sub_menu_name','preview_image')
    search_fields=('id','sub_menu_name','menu_name')
    readonly_fields= ('preview_image',)

    def preview_image(self, obj):
        if obj.sub_menu_image:
            return mark_safe(f'<img src="{obj.sub_menu_image.url}" style="max-width: 200px; max-height: 150px;">')
        else:
            return 'No image found'

class ItemAdmin(admin.ModelAdmin):
    list_display=('id','menu','submenu','item_name','type','price','rating','is_available','preview_image')
    search_fields=('id','menu','submenu','item_name')
    readonly_fields= ('preview_image',)
    def preview_image(self, obj):
        if obj.item_image:
            return mark_safe(f'<img src="{obj.item_image.url}" style="max-width: 200px; max-height: 150px;">')
        else:
            return 'No image found'

class CartAdmin(admin.ModelAdmin):
    list_display=('user','item','quantity','created_at','updated_at')
    search_fields=('user','item')
    list_filter=('quantity',)

class PricesAdmin(admin.ModelAdmin):
    list_display = ('price_type', 'value_type', 'value', 'description', 'created_at', 'updated_at')
    list_filter = ('price_type', 'value_type', 'created_at')
    search_fields = ('price_type', 'description')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'amount', 'status', 'payment_date')
    search_fields = ('transaction_id', 'user__email')
    list_filter = ('status', 'payment_method')
    ordering = ('-payment_date',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'total_price','delivery_type','status','customer_status','created_at', 'updated_at')
    search_fields = ('order_id', 'user__email')
    list_filter = ('status',)
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('items')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'status', 'refund_date')
    search_fields = ('order__order_id', 'status')
    list_filter = ('status',)
    ordering = ('-refund_date',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item', 'quantity', 'price_at_purchase', 'total_price',)
    search_fields = ('order__order_id', 'item__item_name')
    list_filter = ('order__status',)
    ordering = ('order',)

class OrderAdditionalChargesAdmin(admin.ModelAdmin):
    list_display = ('order', 'charge_type', 'value_type', 'value', 'calculated_value', 'created_at')
    list_filter = ('charge_type', 'value_type')
    search_fields = ('order__order_id', 'charge_type')
    readonly_fields = ('calculated_value', 'created_at')

    def save_model(self, request, obj, form, change):
        base_total = sum(item.total_price for item in obj.order.orderitem_set.all())
        obj.calculate_charge(base_total)
        super().save_model(request, obj, form, change)

@admin.register(DeliveryLocation)
class DeliveryLocationAdmin(admin.ModelAdmin):
    list_display=('location_id','location_name','location_image','preview_image')
    search_fields=('location_id','location_name')
    readonly_fields= ('preview_image',)

    def preview_image(self, obj):
        if obj.location_image:
            return mark_safe(f'<img src="{obj.location_image.url}" style="max-width: 200px; max-height: 150px;">')
        else:
            return 'No image found'

admin.site.register(OrderAdditionalCharges, OrderAdditionalChargesAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(FailedLoginAttempts)
admin.site.register(DeliveryPerson, CustomUserAdmin)
admin.site.register(RegularUser, CustomUserAdmin)
admin.site.register(Admin, CustomUserAdmin)
admin.site.register(EmailVerification,EmailVerificationAdmin)
admin.site.register(Menu,MenuAdmin)
admin.site.register(SubMenu,SubMenuAdmin)
admin.site.register(Item,ItemAdmin)
admin.site.register(Cart,CartAdmin)
admin.site.register(Prices,PricesAdmin)