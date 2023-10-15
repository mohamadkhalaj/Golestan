from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db import models
from django.db.models import Sum


# Create your models here.
class Setting(models.Model):
    rate_limit = models.FloatField()

    def __str__(self):
        return "setting"

    @staticmethod
    def total_requests():
        return Student.objects.aggregate(Sum('total_tries'))['total_tries__sum']

    @staticmethod
    def total_users():
        return Student.objects.count()


class Student(models.Model):
    stun = models.CharField(max_length=10, primary_key=True, verbose_name='Student number')
    name = models.CharField(max_length=256, verbose_name='Student name')
    last_try = models.DateTimeField(auto_now=True)
    total_tries = models.PositiveBigIntegerField(default=0, editable=False)

    def humanize_time(self):
        return naturaltime(self.last_try)

    humanize_time.short_description = "Last try"

    def __str__(self):
        return self.stun


def get_rate_limit():
    try:
        return Setting.objects.first().rate_limit
    except:
        Setting.objects.create(rate_limit=2)
        return 2
