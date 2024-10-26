from datetime import timedelta
from .models import IncomeExpense

def calculate_balance(income_expenses):
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

def get_all_income_expense_with_balance():
    from .models import IncomeExpense
    income_expenses = IncomeExpense.objects.all().order_by('date')

    # Use the same balance calculation logic
    return calculate_balance(income_expenses)


def get_income_expense_by_day(user, date):
    """
    Returns a list of all IncomeExpense objects for a given day.

    Args:
        user: The user for whom to retrieve the records.
        date: The specific date for which to retrieve the records.

    Returns:
        QuerySet: A list of IncomeExpense objects for the given day.
    """
    return IncomeExpense.objects.filter(user_id=user, date=date).order_by(
        'date')


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
        total_balance = sum(item['amount'] if item['type'] == 'Income' else -item['amount'] for item in daily_balance)
        total_balance_amount = abs(total_balance)

        balance_last_7_days.append({
            'date': current_day,
            'total_balance': total_balance,
            'total_balance_amount': total_balance_amount
        })

    return balance_last_7_days

