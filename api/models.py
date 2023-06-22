from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db import models


# Create your models here.
class setting(models.Model):
    rateLimit = models.FloatField()

    def __str__(self):
        return "setting"


class student(models.Model):
    stun = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=256)
    lastTry = models.DateTimeField(auto_now=True)

    def humanizeTime(self):
        return naturaltime(self.lastTry)

    humanizeTime.short_description = "Last try"

    def __str__(self):
        return self.stun


def get_rate_limit():
    try:
        return setting.objects.get(pk=1).rateLimit
    except:
        setting.objects.create(rateLimit=2)
        return 2
