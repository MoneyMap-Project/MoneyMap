from django.urls import path

from . import views

app_name = "moneymap"
urlpatterns = [
    path('', views.home, name='home'),
]