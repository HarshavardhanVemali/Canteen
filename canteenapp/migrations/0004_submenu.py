# Generated by Django 5.1.1 on 2024-10-09 07:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('canteenapp', '0003_menu'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubMenu',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('sub_menu_name', models.CharField(blank=True, max_length=100, null=True)),
                ('sub_menu_image', models.ImageField(blank=True, null=True, upload_to='submenu_pics/')),
                ('menu_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='canteenapp.menu')),
            ],
        ),
    ]
