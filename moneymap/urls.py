"""URLs for the moneymap app."""

from django.urls import path

from . import views

app_name = "moneymap"   # pylint: disable=C0103

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('income-expenses/', views.IncomeAndExpensesView.as_view(),
         name='income-expenses'),
    path('goals/', views.goals, name='goals'),
    path('income-and-expenses/history/', views.history_view, name='history'),
    path('income-and-expenses/money-flow/', views.MoneyFlowView.as_view(),
         name='money-flow'),
    path('income-and-expenses/delete/<int:income_expense_id>/',
         views.delete_income_expense, name='delete_income_expense'),
    path('income-expenses/<str:date>/',
         views.IncomeAndExpensesDetailView.as_view(),
         name='income-expense-detail'),
]
