# Generated by Django 5.1.1 on 2024-12-10 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('canteenapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(default='confirmed', max_length=50),
        ),
    ]