# Generated by Django 5.1.1 on 2024-10-12 04:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('canteenapp', '0010_order_delivery_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='customer_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
    ]
