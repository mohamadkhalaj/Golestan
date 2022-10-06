from django.urls import path

from .views import Api

app_name = 'api'
urlpatterns = [
    path('', Api, name='api'),
]
