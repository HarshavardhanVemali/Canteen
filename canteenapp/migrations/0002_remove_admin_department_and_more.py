# Generated by Django 5.1.1 on 2024-10-08 08:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('canteenapp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='admin',
            name='department',
        ),
        migrations.RemoveField(
            model_name='deliveryperson',
            name='delivery_radius',
        ),
        migrations.RemoveField(
            model_name='deliveryperson',
            name='vehicle_info',
        ),
    ]
