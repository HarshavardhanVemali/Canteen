from django.db import models,transaction
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid
from django.utils.timezone import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.core.exceptions import ValidationError
import random
import string
import datetime
from django.utils.timezone import now
from django.db.models import F

class FailedLoginAttempts(models.Model):
    device_id = models.CharField(max_length=255, unique=True)
    attempts = models.PositiveBigIntegerField(default=0)
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.device_id} - Attempts: {self.attempts}'

class CustomUser(AbstractUser):
    DELIVERY_CHOICES = [
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
        ('dining', 'Dining'),
    ]
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='pickup')

    ROLE_CHOICES = [
        ('user', 'User'),
        ('delivery_person', 'Delivery Person'),
        ('admin', 'Admin'),
        ('restaurant', 'Restaurant'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    address = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return self.email 

    class Meta:
        verbose_name = 'CustomUser'
        verbose_name_plural = 'CustomUsers'

class DeliveryPerson(CustomUser):

    class Meta:
        verbose_name = 'Delivery Person'
        verbose_name_plural = 'Delivery Persons'

class RegularUser(CustomUser):
    class Meta:
        verbose_name = 'Regular User'
        verbose_name_plural = 'Regular Users'

class Admin(CustomUser):
    class Meta:
        verbose_name = 'Admin'
        verbose_name_plural = 'Admins'

class EmailVerification(models.Model):
    email = models.EmailField()
    verification_code = models.CharField(max_length=64, unique=True)  
    created_at = models.DateTimeField(auto_now_add=True)  
    expires_at = models.DateTimeField() 
    request_id = models.CharField(max_length=128, unique=True) 
    is_verified = models.BooleanField(default=False) 

    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = uuid.uuid4().hex
        
        if not self.request_id:
            self.request_id = uuid.uuid4().hex
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        if self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Verification for {self.email} - {'Verified' if self.is_verified else 'Pending'}"
    
class Menu(models.Model):
    id=models.AutoField(primary_key=True)
    menu_name=models.CharField(max_length=50,null=True,blank=True)
    menu_image=models.ImageField(upload_to='menu_pics/',blank=True,null=True)
    schedule_time=models.TimeField(null=True,blank=True)

    class Meta:
        unique_together = ('id','menu_name')
    def __str__(self):
        return self.menu_name
    
class SubMenu(models.Model):
    id=models.AutoField(primary_key=True)
    menu_name=models.ForeignKey(Menu,on_delete=models.CASCADE)
    sub_menu_name=models.CharField(max_length=100,null=True,blank=True)
    sub_menu_image=models.ImageField(upload_to='submenu_pics/',blank=True,null=True)
    def __str__(self):
        return self.sub_menu_name

class Restaurant(CustomUser):
    restaurant_name=models.TextField(max_length=50,null=True,blank=True)
    restaurant_image=models.ImageField(upload_to='resturant_pics/',blank=True,null=True)
    
    def __str__(self):
        return self.restaurant_name
    
class Item(models.Model):
    id = models.AutoField(primary_key=True)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, null=True, blank=True)
    submenu = models.ForeignKey(SubMenu, on_delete=models.CASCADE, null=True, blank=True)
    item_name = models.CharField(max_length=100)
    description = models.TextField(blank=True) 
    resturant=models.ForeignKey(Restaurant,on_delete=models.CASCADE,null=True,blank=True)
    TYPE=(
        ('veg','VEG'),
        ('non_veg','NON VEG')
    )
    preparation_time = models.CharField(max_length=50, blank=True)
    serving_size = models.CharField(max_length=50, blank=True)
    type = models.CharField(max_length=20, choices=TYPE)
    price = models.DecimalField(max_digits=8, decimal_places=2) 
    item_image = models.ImageField(upload_to='item_pics/', blank=True, null=True)
    rating=models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_available = models.BooleanField(default=True) 

    def __str__(self):
        return self.item_name

class Cart(models.Model):
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    price_snapshot = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    def __str__(self):
        return f"{self.user.email}'s cart: {self.item.item_name} (Quantity: {self.quantity})"

    class Meta:
        unique_together = ('user', 'item')

    def save(self, *args, **kwargs):
        if not self.price_snapshot: 
             self.price_snapshot = self.item.price
        super().save(*args, **kwargs)

class Prices(models.Model):
    PRICE_TYPE_CHOICES = [
        ('GST', 'GST'),
        ('Delivery', 'Delivery Charge'),
        ('Service', 'Service Charge'),
        ('Packaging', 'Packaging Charge'),
        ('PlatFormFee','PlatForm Fee'),
        ('Other', 'Other'),
    ]
    VALUE_TYPE_CHOICES = [
        ('Price', 'Fixed Price'),
        ('Percentage', 'Percentage'),
    ]
    price_type = models.CharField(max_length=20, choices=PRICE_TYPE_CHOICES, default='GST')
    value_type = models.CharField(max_length=10, choices=VALUE_TYPE_CHOICES, default='Price') 
    value = models.DecimalField(max_digits=10, decimal_places=2)  
    description = models.TextField(null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.price_type} - {self.value} ({self.get_value_type_display()})"

    def calculate_charge(self, base_amount):
        if self.value_type == 'Percentage':
            return (self.value / 100) * base_amount
        return self.value  
    
class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('upi', 'UPI'),
        ('debit_card', 'Debit Card'),
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    transaction_id = models.CharField(max_length=255, unique=True)
    order_id = models.CharField(max_length=255, unique=True) 
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(auto_now_add=True)
    response_code = models.CharField(max_length=10, null=True, blank=True) 
    message = models.TextField(null=True, blank=True) 
    payment_instrument = models.CharField(max_length=255, null=True, blank=True) 
    phonepe_transaction_id = models.CharField(max_length=255, null=True, blank=True)  

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"

    def is_successful(self):
        return self.status == 'success'

def generate_order_id():
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    random_string=''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    order_id = f"{timestamp}{random_string}"
    return order_id

class Refund(models.Model):
    REFUND_STATUS_CHOICES = [
        ('initiated', 'Refund Initiated'),
        ('success', 'Refund Success'),
        ('failed', 'Refund Failed'),
    ]
    
    order = models.OneToOneField('Order', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='initiated')
    refund_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refund for Order {self.order.order_id} - Status: {self.status}"
    def save(self, *args, **kwargs):
        if not self.amount:
            self.amount = self.order.total_price
        super().save(*args, **kwargs)

class Order(models.Model):    
    CUSTOMER_ORDER_STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    DELIVERY_CHOICES = [
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
        ('dining', 'Dining'),
    ]
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('prepared', 'Prepared'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PICKUP_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready_to_take', 'Ready to Take'),
        ('delivered', 'Received by Customer'),
        ('cancelled', 'Cancelled'),
    ]
    
    DINING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('delivered', 'Served to Customer'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    payment = models.OneToOneField('Payment', on_delete=models.PROTECT, null=True, blank=True) 
    items = models.ManyToManyField('Item', through='OrderItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=50, default='confirmed')
    customer_status = models.CharField(max_length=20, default='pending')
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='pickup')  
    delivery_person = models.ForeignKey(DeliveryPerson, blank=True, null=True, on_delete=models.SET_NULL, related_name='orders_as_delivery_person')
    cancel_reason = models.TextField(blank=True)
    delivery_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    daily_sequence = models.PositiveIntegerField(blank=True, null=True) 
    order_id = models.CharField(max_length=20, unique=True, editable=False, default=generate_order_id)
    restaurant=models.ForeignKey(Restaurant,on_delete=models.CASCADE,null=True,blank=True,related_name='ordered_restaurant')

    def __str__(self):
        return f"Order {self.order_id} by {self.user.email} - {self.status}"

    def can_place_order(self):
        return self.payment and self.payment.is_successful() 
    @transaction.atomic
    def create_order_from_cart(self, cart_items):
        """Atomically creates an order from cart items."""
        total_price = 0
        order_items_to_create = []

        for cart_item in cart_items:
            try:
                item = Item.objects.select_for_update().get(
                    id=cart_item.item_id,
                    price=cart_item.price_snapshot,
                    is_available=True
                )
            except Item.DoesNotExist:
                raise ValidationError(f"Item {cart_item.item.item_name} is unavailable or its price has changed.")
            item.save()

            order_item = OrderItem(
                order=self,
                item=item,
                quantity=cart_item.quantity,
                price_at_purchase=cart_item.price_snapshot
            )
            order_items_to_create.append(order_item)
            total_price += order_item.calculate_total_price()
        self.total_price = total_price
        self.save()  
        OrderItem.objects.bulk_create(order_items_to_create)
        cart_items.delete()

        self.add_additional_charges()
        self.calculate_total_price()
    def cancel_order(self):
        if self.status == 'cancelled':
            raise ValidationError("Order is already cancelled.")

        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()
        Refund.objects.create(
            order=self,
            amount=self.total_price,
            status='initiated'
        )


    def get_status_display(self):
        if self.delivery_type == 'delivery':
            status_choices = self.DELIVERY_STATUS_CHOICES
        elif self.delivery_type == 'pickup':
            status_choices = self.PICKUP_STATUS_CHOICES
        elif self.delivery_type == 'dining':
            status_choices = self.DINING_STATUS_CHOICES
        else:
            status_choices = [] 

        for status_tuple in status_choices:
            if status_tuple[0] == self.status:
                return status_tuple[1]

        return self.status 

    def clean(self):
        if self.pk and self.payment: 
            if Order.objects.filter(payment__transaction_id=self.payment.transaction_id).exclude(pk=self.pk).exists():
                raise ValidationError("An order with this transaction ID already exists.")
    def add_additional_charges(self):
        if not self.pk:
            return
        base_total = sum(item.total_price for item in self.orderitem_set.all()) 

        if self.delivery_type == 'delivery':
            additional_charges_to_add = ['Delivery', 'Packaging']
        elif self.delivery_type == 'dining':
            additional_charges_to_add = ['Service']
        elif self.delivery_type == 'pickup':
            additional_charges_to_add = ['Packaging']
        else:
            additional_charges_to_add = []

        for charge_type in additional_charges_to_add:
            try:
                price = Prices.objects.get(price_type=charge_type)
                additional_charge = OrderAdditionalCharges(
                    order=self,
                    charge_type=charge_type,
                    value_type=price.value_type,
                    value=price.value, 
                )
                additional_charge.save()
            except Prices.DoesNotExist:
                print(f"Warning: Price for {charge_type} not found in database.")
    
    def calculate_total_price(self):
        if not self.pk:
            return  

        total = sum(item.total_price for item in self.orderitem_set.all())
        additional_charges = sum(charge.calculated_value for charge in self.additional_charges.all())
        self.total_price = total + additional_charges
    
    def save(self, *args, **kwargs):
        self.clean() 
        if self.status == 'delivered' and self.delivery_type == 'delivery':
            self.delivered_at = timezone.now()
        elif self.status == 'delivered' and self.delivery_type == 'dining':
            self.delivered_at = timezone.now() 
        elif self.status == 'received' and self.delivery_type == 'pickup':
            self.delivered_at = timezone.now() 
        elif self.status == 'cancelled':
            self.cancelled_at = timezone.now()

        if self.customer_status == 'pending' and self.created_at is not None: 
            time_diff = (timezone.now() - self.created_at).total_seconds()
            two_minutes = 120
            if time_diff > two_minutes:
                self.customer_status = 'confirmed'
        
        if not self.daily_sequence:
            today_date = now().date()
            max_sequence = Order.objects.filter(
                created_at__date=today_date
            ).aggregate(models.Max('daily_sequence'))['daily_sequence__max']
            self.daily_sequence = (max_sequence or 0) + 1
        if not self.pk:  
            self.calculate_total_price() 
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey('Item', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.item.item_name} in Order {self.order.order_id}"
    
    def calculate_total_price(self):
        self.total_price = self.quantity * self.price_at_purchase
        return self.total_price

    def save(self, *args, **kwargs):
        self.calculate_total_price() 
        super().save(*args, **kwargs)

class OrderAdditionalCharges(models.Model):
    PRICE_TYPE_CHOICES = [
        ('GST', 'GST'),
        ('Delivery', 'Delivery Charge'),
        ('Service', 'Service Charge'),
        ('Packaging', 'Packaging Charge'),
        ('PlatFormFee','PlatForm Fee'),
        ('Other', 'Other'),
    ]
    VALUE_TYPE_CHOICES = [
        ('Price', 'Fixed Price'),
        ('Percentage', 'Percentage'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='additional_charges')
    charge_type = models.CharField(max_length=20, choices=PRICE_TYPE_CHOICES)
    value_type = models.CharField(max_length=10, choices=VALUE_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    calculated_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.charge_type} - {self.calculated_value} for Order {self.order.order_id}"

    def calculate_charge(self, base_total):
        if self.value_type == 'percentage':
            self.calculated_value = (self.value / 100) * base_total
        else:
            self.calculated_value = self.value
        return self.calculated_value

    def save(self, *args, **kwargs):
        base_total = sum(item.total_price for item in self.order.orderitem_set.all())
        self.calculate_charge(base_total)
        super().save(*args, **kwargs)
        self.order.calculate_total_price()

class DeliveryLocation(models.Model):
    location_id=models.AutoField(primary_key=True)
    location_name=models.CharField(max_length=100,null=True,blank=True)
    location_image=models.ImageField(upload_to='location_pics/', blank=True, null=True)
    
    def __str__(self):
        return self.location_name