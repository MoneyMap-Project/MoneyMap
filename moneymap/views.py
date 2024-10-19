from django.utils import timezone
from urllib import request
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect

from .models import IncomeExpense
from django.contrib import messages


def is_admin(user):
    return user.is_superuser  # Check if the user is a superuser


def home(request):
    return render(request, 'moneymap/home.html')


def income_and_expenses(request):
    return render(request, 'moneymap/income-expenses.html')


def goals(request):
    return render(request, 'moneymap/goals.html')


def history(request):
    return render(request, 'moneymap/history.html')


def income_expense_view(request):
    if request.method == 'POST':
        # Get data from the form
        selected_type = request.POST.get('money_type')
        amount = request.POST.get('amount')
        description = request.POST.get('description')

        # Print local variables for debugging
        print(f"Expense Type: {selected_type}")
        print(f"Amount: {amount}")
        print(f"Description: {description}")

    return render(request, 'moneymap/money-flow.html')
