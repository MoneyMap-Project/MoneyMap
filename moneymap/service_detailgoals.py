"""Service functions for the MoneyMap goal page."""

from decimal import Decimal, ROUND_CEILING
import logging
from django.db.models import Sum, F
from django.utils import timezone
from .models import Goal, IncomeExpense
# from .service_addgoals import calculate_days_remaining


def calculate_days_remaining(end_date):
    """Calculate the days remaining until the goal deadline."""
    return max((end_date - timezone.now().date()).days, 0)


def calculate_trend(goal_id):
    """
    Calculate the trend for the goal.

    Args:
        user: The user for whom to retrieve the records.
        date: The specific date for which to retrieve the records.

    Returns:
        list: A list of dictionaries containing goal_id and their respective trends.
    """
    # if shortfall >= 0, trend is positive, otherwise negative

    if calculate_saving_shortfall(goal_id) <= 0:
        trend = 'Positive'
    else:
        trend = 'Negative'
    return [{'goal_id': goal_id, 'trend': trend}]

def calculate_saving_progress(goal: Goal) -> Decimal:
    """Calculate the saving progress as a percentage of the current amount towards the target amount."""
    if goal.target_amount <= 0:
        return Decimal('0.00')  # Avoid division by zero

    progress_percentage = (goal.current_amount / goal.target_amount) * 100
    # 2 decimal places
    # return progress_percentage.quantize(Decimal('0.01'),
    #                                     rounding=ROUND_CEILING)
    return round(progress_percentage, 2)


def calculate_days_elapsed(date, goal):
    """ Calculate how many days have passed since the goal started"""
    days_elapsed = max(0, (
            date - goal.start_date).days)  # max to avoid negative days
    return days_elapsed


def calculate_avg_saving(user, date, goal_id):
    """
    Calculate the average daily saving been saved so far
    for the specified goal.
    """
    try:
        goal = Goal.objects.get(goal_id=goal_id, user_id=user)
        days_so_far = calculate_days_elapsed(date, goal)

        # Calculate average saving
        avg_saving = goal.current_amount / days_so_far if days_so_far > 0 else goal.current_amount
        # logging.info(f"Day so far: {days_so_far}, avg_saving: {avg_saving}, goal.current_amount: {goal.current_amount}, goal.target_amount: {goal.target_amount}")

        # 2 decimal places
        return round(avg_saving, 2)

    except Goal.DoesNotExist:
        return Decimal('0.00').quantize(Decimal('0.01'),
                                        rounding=ROUND_CEILING)  # Goal not found

def calculate_saving_shortfall(goal_id):
    """Calculate the extra daily saving needed to meet the goal."""
    # target_amount / days_remaining - income saving date=localtime.date.today

    try:
        saving_today = get_total_today_saving(goal_id)
        target_amount = Goal.objects.get(goal_id=goal_id).target_amount
        days_remaining = calculate_days_remaining(Goal.objects.get(goal_id=goal_id).end_date)
        # logging.debug(f"Saving today: {saving_today}, Target amount: {target_amount}, Days remaining: {days_remaining}")

        if days_remaining > 0:
            # Calculate shortfall "extra saving needed per day"
            shortfall = (target_amount / days_remaining) - saving_today
            # logging.debug(f"Shortfall: {shortfall}")
            return round(max(Decimal('0.00'), shortfall), 2)  # Return 0 if no shortfall
        else:
            return 0.00
    except Goal.DoesNotExist:
        return 0.00  # Goal not found


def get_total_today_saving(goal_id):
    """Get the total saving amount of today saving."""
    today_date = timezone.localtime(timezone.now()).date()
    # goal_name = get_goal_title_from_IncomeExpense_table()
    saving_today = (
            IncomeExpense.objects.filter(
                type='saving',
                goal__goal_id=goal_id,
                date=today_date
            )
            .aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    )
    # logging.debug(f"Total saving today: {saving_today}")
    return saving_today

def get_all_saving_specific_goal(goal_title):
    """Get all saving records for a specific goal.

    Args:
        goal_title (str): The title of the goal to match.

    Returns:
        QuerySet: A list of IncomeExpense objects for the goal.
    """
    savings = IncomeExpense.objects.filter(
        type='saving',
        description=f"Saving money to {goal_title}"
    ).values('date', __amount=F('amount'))  # Get date and amount as dictionary fields

    # logging.debug(f"Fetched savings for goal '{goal_title}': {list(savings)}")
    return savings

def get_all_goals(user):
    """
    Get all goals for the user.

    Args:
        user: The user for whom to retrieve the records.

    Returns:
        QuerySet: A list of Goal objects for the given user.
    """
    return Goal.objects.filter(user_id=user)

def get_current_total_days(goal, date):
    """Calculate the total days between the start date and the current date."""
    return (date - goal.start_date).days + 1
