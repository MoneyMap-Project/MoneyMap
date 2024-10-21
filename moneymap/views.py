from django.shortcuts import render, redirect

from .models import IncomeExpense
from django.contrib import messages
from django.utils import timezone


def is_admin(user):
    return user.is_superuser  # Check if the user is a superuser


def home(request):
    return render(request, 'moneymap/home.html')


def income_and_expenses_view(request):
    today = timezone.now().date()
    # Retrieve all IncomeExpense records created today
    income_expenses = IncomeExpense.objects.all().filter(date=today)
    # income_expenses = IncomeExpense.objects.filter(user_id=request.user).order_by('-date')  # TODO: implement with user_id
    return render(request, 'moneymap/income-expenses.html',
                  {'income_expenses': income_expenses})


def goals(request):
    return render(request, 'moneymap/goals.html')


def history(request):
    return render(request, 'moneymap/history.html')


def moneyflow_view(request):
    if request.method == 'POST':
        # Get data from the form
        selected_type = request.POST.get('money_type')
        amount = request.POST.get('amount')
        description = request.POST.get('description')

        try:
            amount_decimal = float(amount)
            print(f"Converted amount: {amount_decimal}")

            # Create and save a new IncomeExpense object
            new_income_expense = IncomeExpense.objects.create(
                user_id=None,  # Set to None since there's no user
                type=selected_type,
                amount=amount_decimal,
                date=timezone.now(),
                description=description,
            )
            print(f"New IncomeExpense object created: {new_income_expense}")

            messages.success(request, 'Income/Expense recorded successfully!')
            return redirect('moneymap:money-flow')
        except ValueError as ve:
            messages.error(request, 'Invalid amount entered. Please enter a valid number.')
            print(f"ValueError: {ve}")
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            print(f"Exception: {e}")

    return render(request, 'moneymap/money-flow.html')
