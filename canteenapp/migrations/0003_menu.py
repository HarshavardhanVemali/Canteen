# Generated by Django 5.1.1 on 2024-10-09 04:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('canteenapp', '0002_remove_admin_department_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('menu_name', models.CharField(blank=True, max_length=50, null=True)),
                ('menu_image', models.ImageField(blank=True, null=True, upload_to='menu_pics/')),
                ('schedule_time', models.TimeField(blank=True, null=True)),
            ],
            options={
                'unique_together': {('id', 'menu_name')},
            },
        ),
    ]
