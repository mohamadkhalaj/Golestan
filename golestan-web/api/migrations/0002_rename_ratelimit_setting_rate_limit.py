# Generated by Django 4.0.7 on 2023-06-30 19:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='setting',
            old_name='rateLimit',
            new_name='rate_limit',
        ),
    ]