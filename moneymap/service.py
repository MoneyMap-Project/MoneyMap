"""Service functions for the MoneyMap view."""

from datetime import timedelta
from .models import IncomeExpense
from decimal import Decimal


def calculate_balance(income_expenses):
    """Calculate the balance based on income and expenses."""
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
            'date': item.date,
            'IncomeExpense_id': item.IncomeExpense_id,
            'description': item.description,
            'amount': item.amount,
            'balance': abs(balance),
            'type': item.type,
            'check': check,
        })

    return income_expense_with_balance


def get_income_expense_by_day(user, date):
    """
    Returns a list of all IncomeExpense objects for a given day.

    Args:
        user: The user for whom to retrieve the records.
        date: The specific date for which to retrieve the records.

    Returns:
        QuerySet: A list of IncomeExpense objects for the given day.
    """
    return IncomeExpense.objects.filter(user_id=user, date=date).order_by('date')


def calculate_balance_last_7_days(user, today):
    """
    Returns a list of total balances for each of the last 7 days (including today).

    Args:
        user: The user for whom to retrieve the records.
        today: The current date.

    Returns:
        List[Dict]: A list where each item contains the total balance and date for the last 7 days.
    """
    balance_last_7_days = []

    for last_day in range(7):
        current_day = today - timedelta(days=last_day)

        # Get all IncomeExpense objects for the current day
        income_expenses = get_income_expense_by_day(user, current_day)

        # Calculate the balance for the current day
        daily_balance = calculate_balance(income_expenses)

        # Calculate the total balance for the day by summing the 'amount' field
        total_balance = sum(
            item['amount'] if item['type'] == 'Income' else -item['amount'] for
            item in daily_balance)
        total_balance_amount = abs(total_balance)

        balance_last_7_days.append({
            'date': current_day,
            'total_balance': total_balance,
            'total_balance_amount': total_balance_amount
        })

    return balance_last_7_days


def sum_income(user, date):
    """Get summation of type 'Income' for a specific day."""
    income = IncomeExpense.objects.filter(user_id=user, date=date, type='Income')
    return sum(item.amount for item in income)


def sum_expense(user, date):
    """Get summation of type 'Expense' for a specific day."""
    expenses = IncomeExpense.objects.filter(user_id=user, date=date, type='Expenses')
    return sum(item.amount for item in expenses)


def sum_income_by_month(user, month):
    """Get summation of type 'Income' for a specific month."""
    income = IncomeExpense.objects.filter(user_id=user, date__month=month, type='Income')
    return sum(item.amount for item in income)


def sum_expense_by_month(user, month):
    """Get summation of type 'Expense' for a specific month."""
    expenses = IncomeExpense.objects.filter(user_id=user, date__month=month, type='Expenses')
    return sum(item.amount for item in expenses)


def calculate_income_expense_percentage(month_income, month_expense):
    """Calculate income and expense percentages based on monthly totals."""
    total = month_income + month_expense
    if total == 0:
        return {'income_percent': 0, 'expense_percent': 0}

    income_percent = (month_income / total) * 100
    expense_percent = (month_expense / total) * 100

    return {
        'income_percent': round(income_percent, 2),
        'expense_percent': round(expense_percent, 2)
    }


def update_current_amount(self, amount_saved):
    """Update current amount with a new saving input."""
    self.current_amount += Decimal(amount_saved)
    self.save()

def remaining_amount(self):
    """Calculate remaining amount to reach target."""
    return max(Decimal('0.00'), self.target_amount - self.current_amount)

def __str__(self):
    return f"{self.description}"
