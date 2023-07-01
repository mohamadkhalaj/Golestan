from django.contrib import admin

from .models import Setting, Student

# Register your models here.

admin.site.site_header = 'Golestan API management system'


class SettingAdmin(admin.ModelAdmin):
    list_display = ('rate_limit', 'total_requests', 'total_users')


admin.site.register(Setting, SettingAdmin)


class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'stun', 'humanize_time', 'total_tries')
    list_filter = ('last_try',)
    search_fields = ('name', 'stun')
    ordering = ('-last_try',)


admin.site.register(Student, StudentAdmin)
