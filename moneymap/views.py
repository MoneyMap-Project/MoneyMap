from django.shortcuts import render, redirect

from .models import IncomeExpense
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .utils import calculate_balance


def is_admin(user):
    return user.is_superuser  # Check if the user is a superuser


def home(request):
    return render(request, 'moneymap/home.html')


def income_and_expenses_view(request):
    local_time = timezone.localtime(timezone.now())
    today = local_time.date()

    # Check if user is authenticated
    if request.user.is_authenticated:
        # Retrieve all IncomeExpense records for the logged-in user
        income_expenses = IncomeExpense.objects.filter(user_id=request.user,
                                                       date=today).order_by(
            'date')

        # Use the extracted method to calculate balance
        income_expense_with_balance = calculate_balance(income_expenses)

        return render(request, 'moneymap/income-expenses.html', {
            'income_expense_with_balance': income_expense_with_balance,
            'has_data': bool(income_expense_with_balance),
            # Flag to check if there's data
            'user_id_display': request.user.username
        })
    else:
        # If user is not authenticated, provide a placeholder for user_id_display
        return render(request, 'moneymap/income-expenses.html', {
            'income_expense_with_balance': [],
            'has_data': False,
            'user_id_display': 'guest'
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
