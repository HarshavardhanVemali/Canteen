# Generated by Django 5.1.1 on 2024-10-12 08:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('canteenapp', '0012_order_cancel_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='confirmed_at',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='shipped_at',
            field=models.DateField(blank=True, null=True),
        ),
    ]
