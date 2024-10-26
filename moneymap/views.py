from django.shortcuts import render, redirect, get_object_or_404

from .models import IncomeExpense
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .utils import calculate_balance, calculate_balance_last_7_days

def is_admin(user):
    return user.is_superuser  # Check if the user is a superuser


def home(request):
    return render(request, 'moneymap/home.html')


def income_and_expenses_view(request):
    local_time = timezone.localtime(timezone.now())
    today = local_time.date()

    # Check if user is authenticated
    if request.user.is_authenticated:
        # Retrieve income/expense records for today
        income_expenses_today = IncomeExpense.objects.filter(
            user_id=request.user,
            date=today
        ).order_by('date')

        # Use the function to calculate balance for the last 7 days
        income_expense_with_balance_last_7_days = calculate_balance_last_7_days(request.user, today)

        # Calculate today's balance separately
        income_expense_with_balance_today = calculate_balance(income_expenses_today)

        return render(request, 'moneymap/income-expenses.html', {
            'income_expense_with_balance_today': income_expense_with_balance_today,
            'income_expense_with_balance_last_7_days': income_expense_with_balance_last_7_days,
            'has_data': bool(income_expense_with_balance_today),
            'user_id_display': request.user.username
        })
    else:
        # If user is not authenticated, provide a placeholder for user_id_display
        return render(request, 'moneymap/income-expenses.html', {
            'income_expense_with_balance_today': [],
            'income_expense_with_balance_last_7_days': [],
            'has_data': False,
            'user_id_display': 'guest'
        })


@login_required
def delete_income_expense(request, income_expense_id):
    # Retrieve the IncomeExpense object or return 404 if not found
    income_expense = get_object_or_404(IncomeExpense, IncomeExpense_id=income_expense_id, user_id=request.user)

    # Delete the object
    income_expense.delete()

    # Add a success message
    messages.success(request, 'Income/Expense record successfully deleted.')

    # Redirect back to the income and expenses view
    return redirect('moneymap:income-expenses')


@login_required
def income_and_expenses_detail_view(request, date):
    # Convert the date string to a datetime object
    try:
        selected_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return render(request, 'moneymap/error.html',
                      {'message': 'Invalid date format.'})

    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Retrieve IncomeExpense records for the selected date and the logged-in user
        income_expenses = IncomeExpense.objects.filter(user_id=request.user,
                                                       date=selected_date).order_by(
            'date')

        # Use the utility method to calculate the balance for the selected date
        income_expense_with_balance = calculate_balance(income_expenses)

        return render(request, 'moneymap/income-expense-detail.html', {
            'income_expense_with_balance': income_expense_with_balance,
            'selected_date': selected_date
        })
    else:
        return render(request, 'moneymap/error.html',
                      {'message': 'You need to log in to view the details.'})

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
                saved_to_income_expense= True,
                type=selected_type,
                amount=amount_decimal,
                date=timezone.now(),
                description=description,
            )
            print(f"New IncomeExpense object created: {new_income_expense}")

            # messages.success(request, 'Income/Expense recorded successfully!') #TODO change it to log
            return redirect('moneymap:money-flow')
        except ValueError as ve:
            # messages.error(request,
            #                'Invalid amount entered. Please enter a valid number.') #TODO change it to log
            print(f"ValueError: {ve}")
        except Exception as e:
            # messages.error(request, f'An error occurred: {str(e)}') #TODO change it to log
            print(f"Exception: {e}")

    return render(request, 'moneymap/money-flow.html')


def detail(request):
    return render(request, 'moneymap/income-expense-detail.html')
