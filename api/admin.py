from django.contrib import admin

from .models import setting, student

# Register your models here.

admin.site.site_header = 'API management system'


class settingAdmin(admin.ModelAdmin):
    list_display = ('rateLimit',)


admin.site.register(setting, settingAdmin)


class studentAdmin(admin.ModelAdmin):
    list_display = ('name', 'stun', 'humanize_time')
    list_filter = ('stun', 'lastTry')
    search_fields = ('name', 'stun')
    ordering = ('-lastTry',)


admin.site.register(student, studentAdmin)
