# Generated by Django 4.0.7 on 2023-10-15 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_student_total_tries'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='name',
            field=models.CharField(max_length=256, verbose_name='Student name'),
        ),
        migrations.AlterField(
            model_name='student',
            name='stun',
            field=models.CharField(max_length=10, primary_key=True, serialize=False, verbose_name='Student number'),
        ),
        migrations.AlterField(
            model_name='student',
            name='total_tries',
            field=models.PositiveBigIntegerField(default=0, editable=False),
        ),
    ]
