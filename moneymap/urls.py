from django.urls import path

from . import views

app_name = "moneymap"
urlpatterns = [
    path('', views.home, name='home'),
    path('income-and-expenses/', views.income_and_expenses, name='income-expenses'),
    path('goals/', views.goals, name='goals'),
    path('history/', views.history, name='history'),
]