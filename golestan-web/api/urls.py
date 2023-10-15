from django.urls import path

from .views import api

app_name = 'api'
urlpatterns = [
    path('', api, name='api'),
]
