from django.shortcuts import render, redirect

from .models import IncomeExpense
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required


def is_admin(user):
    return user.is_superuser  # Check if the user is a superuser


def home(request):
    return render(request, 'moneymap/home.html')


@login_required
def income_and_expenses_view(request):
    today = timezone.now().date()
    # Retrieve all IncomeExpense records created today for the logged-in user
    income_expenses = IncomeExpense.objects.filter(user_id=request.user,
                                                   date=today).order_by('date',
                                                                        'IncomeExpense_id')

    balance = 0
    check = 0
    income_expense_with_balance = []

    for item in income_expenses:
        # Update balance based on the type of transaction
        if item.type == 'Income':
            balance += item.amount
            check += item.amount
        else:
            balance -= item.amount
            check -= item.amount

        # Add each record along with the updated balance to the list
        income_expense_with_balance.append({
            'description': item.description,
            'amount': item.amount,
            'balance': abs(balance),
            'type': item.type,
            'check': check,
        })

    return render(request, 'moneymap/income-expenses.html', {
        'income_expense_with_balance': income_expense_with_balance
    })


def goals(request):
    return render(request, 'moneymap/goals.html')


def history(request):
    return render(request, 'moneymap/history.html')


@login_required
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
                user_id=request.user,
                type=selected_type,
                amount=amount_decimal,
                date=timezone.now(),
                description=description,
            )
            print(f"New IncomeExpense object created: {new_income_expense}")

            messages.success(request, 'Income/Expense recorded successfully!')
            return redirect('moneymap:money-flow')
        except ValueError as ve:
            messages.error(request,
                           'Invalid amount entered. Please enter a valid number.')
            print(f"ValueError: {ve}")
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            print(f"Exception: {e}")

    return render(request, 'moneymap/money-flow.html')
