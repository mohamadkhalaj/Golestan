# Generated by Django 4.0.7 on 2023-07-01 09:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_rename_lasttry_student_last_try_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='setting',
            name='total_requests',
        ),
    ]
