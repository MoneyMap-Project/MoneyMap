from django.shortcuts import render, redirect, get_object_or_404

from .models import IncomeExpense
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .utils import *

# logger
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
        income_expense_with_balance_last_7_days = calculate_balance_last_7_days(
            request.user, today)

        # Calculate today's balance separately
        income_expense_with_balance_today = calculate_balance(
            income_expenses_today)

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
    income_expense = get_object_or_404(IncomeExpense,
                                       IncomeExpense_id=income_expense_id,
                                       user_id=request.user)

    # Delete the object
    income_expense.delete()

    # Add a success message
    messages.success(request, 'Income/Expense record successfully deleted.')

    # Redirect back to the income and expenses view
    return redirect('moneymap:income-expenses')


def goals(request):
    return render(request, 'moneymap/goals.html')


@login_required
def moneyflow_view(request):
    """
    After clicked the `Income and Expense` button,
    this view will be called
    """
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
                saved_to_income_expense=True,
                type=selected_type,
                amount=amount_decimal,
                date=timezone.now(),
                description=description,
            )
            print(f"New IncomeExpense object created: {new_income_expense}")

            # messages.success(request, 'Income/Expense recorded successfully!') #TODO change it to log
            return redirect('moneymap:income-expenses')
        except ValueError as ve:
            # messages.error(request,
            #                'Invalid amount entered. Please enter a valid number.') #TODO change it to log
            print(f"ValueError: {ve}")
        except Exception as e:
            # messages.error(request, f'An error occurred: {str(e)}') #TODO change it to log
            print(f"Exception: {e}")

    return render(request, 'moneymap/money-flow.html')


@login_required
def income_and_expenses_detail_view(request, date):
    """Income and Expense Report for a specific date"""
    # Convert the date string to a datetime object
    try:
        selected_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        logger.error("Invalid date format.")
        return redirect('moneymap:income-expenses')

    # Retrieve IncomeExpense records for the selected date and the logged-in user
    income_expenses = IncomeExpense.objects.filter(user_id=request.user,
                                                   date=selected_date).order_by('date')

    # Check if there is data and calculate balance if data exists
    if income_expenses.exists():
        income_expense_with_balance = calculate_balance(income_expenses)
        latest_balance = income_expense_with_balance[-1]['balance']
        # logger.debug(f"Latest balance: {latest_balance}")

        # Retrieve only income and expenses using utility functions
        day_income = sum_income(request.user, selected_date)
        # logger.debug(f"Total income: {day_income}")  # 5,020
        day_expense = sum_expense(request.user, selected_date)
        # logger.debug(f"Total income: {day_expense}")  # 117

        month_income = sum_income_by_month(request.user, selected_date.month)
        # logger.debug(f"Total income: {month_income}")  # 5,020
        month_expense = sum_expense_by_month(request.user, selected_date.month)

        month_balance = month_income - month_expense

        percentages = calculate_income_expense_percentage(month_income,
                                                          month_expense)

        has_data = True
    else:
        income_expense_with_balance = None
        latest_balance = 0

        day_income = 0
        day_expense = 0

        month_income = sum_income_by_month(request.user, selected_date.month)
        month_expense = sum_expense_by_month(request.user, selected_date.month)

        month_balance = month_income - month_expense

        percentages = calculate_income_expense_percentage(month_income,
                                                          month_expense)

        has_data = False

    # logger.debug(income_expense_with_balance[1]['type'])

    return render(request, 'moneymap/income-expense-detail.html', {
        'income_expense_with_balance': income_expense_with_balance,
        'selected_date': selected_date,
        'latest_balance': latest_balance,
        'day_income': day_income,
        'day_expense': day_expense,
        'month_income': month_income,
        'month_expense': month_expense,
        'month_balance': month_balance,
        'income_percent': percentages['income_percent'],
        'expense_percent': percentages['expense_percent'],
        'has_data': has_data,
    })


@login_required
def history_view(request):
    """View showing income and expense history, grouped by date"""
    today = timezone.now().date()

    # Get start and end date from GET parameters
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')

    # Check if the dates are provided and parse them
    if start_date and end_date:
        # Convert string dates to date objects
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()

        # Ensure start_date is less than or equal to end_date
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        # Filter the date from the range that user select
        dates = IncomeExpense.objects.filter(user_id=request.user,
                                             date__range=[start_date, end_date]).dates('date', 'day')
    else:
        # Default to show all records if no dates are provided
        dates = IncomeExpense.objects.filter(user_id=request.user).dates('date', 'day')

    history_list = []
    for date in reversed(dates):
        # Get income and expenses for the day using `get_income_expense_by_day`
        income_expenses = get_income_expense_by_day(request.user, date)

        # Calculate the daily income and expense using sum over filtered data
        day_income = sum(entry.amount for entry in income_expenses if entry.type.lower() == 'income')
        day_expense = sum(entry.amount for entry in income_expenses if entry.type.lower() == 'expenses')

        # Calculate total (income - expense) for the day
        total = day_income - day_expense

        # Add the daily record to the history list
        history_list.append({
            'date': date,
            'income': day_income,
            'expense': day_expense,
            'total': total,
        })

    # Render the history list in the template, along with the date range
    return render(request, 'moneymap/history.html', {
        'history_list': history_list,
        'start_date': start_date,
        'end_date': end_date,
    })