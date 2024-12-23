"""URLs for the moneymap app."""

from django.urls import path

from . import views

app_name = "moneymap"  # pylint: disable=C0103
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('income-expenses/', views.IncomeAndExpensesView.as_view(),
         name='income-expenses'),
    path('income-expenses/add-tag', views.AddTagView.as_view(),
         name='add_tag'),
    path('income-expenses/delete-tag', views.DeleteTagView.as_view(),
         name='delete_tag'),
    path('goals/', views.GoalView.as_view(), name='goals'),
    path('goals/add-money', views.AddSavingMoney.as_view(), name='add_money_goals'),
    # path('goals/detail', views.GoalsDetail.as_view(), name='goal_detail'),
    path('goals/detail/<int:pk>/', views.GoalsDetailView.as_view(),
         name='goal-detail'),
    path('goals/<int:goal_id>/delete/', views.delete_goal, name='delete_goal'),
    path('goals/add', views.AddGoals.as_view(), name='add_goals'),
    path('income-and-expenses/history/', views.HistoryView.as_view(),
         name='history'),
    path('income-and-expenses/money-flow/', views.MoneyFlowView.as_view(),
         name='money-flow'),
    path('income-and-expenses/delete/<int:income_expense_id>/',
         views.delete_income_expense, name='delete_income_expense'),
    path('income-expenses/<str:date>/',
         views.IncomeAndExpensesDetailView.as_view(),
         name='income-expense-detail'),
]
