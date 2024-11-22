"""Service functions for the MoneyMap goal page."""

from datetime import timedelta, datetime
from django.db.models import Sum, F
from django.utils import timezone
from .models import Goal, IncomeExpense
from decimal import Decimal, ROUND_CEILING, InvalidOperation
from django.db.models import Avg, Min

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta


def calculate_days_remaining(user, date, goal_id):   #TODO: We also have `days_remaining` method in the Goal model.
    """
    Calculate the days remaining to reach a specific goal for a user.

    Args:
        user: The user for whom to retrieve the records.
        date: The specific date for which to calculate the remaining days. [must be current date]
        goal_id: The ID of the specific goal for which to calculate remaining days.

    Returns:
        int: The number of days remaining to reach the specified goal, or None if the goal is not found or 0 if already past.
    """
    try:
        goal = Goal.objects.get(user_id=user, goal_id=goal_id)

        # Check if the goal's end date is in the future
        if goal.end_date >= date:
            days_remaining = (goal.end_date - date).days
            return days_remaining
        else:
            return 0  # Goal is already past

    except Goal.DoesNotExist:
        return None  # Goal not found


def calculate_trend(user, date):
    """
    Calculate the trend for the goal.

    Args:
        user: The user for whom to retrieve the records.
        date: The specific date for which to retrieve the records.

    Returns:
        list: A list of dictionaries containing goal_id and their respective trends.
    """
    # logging.info(f"Calculating trend for user {user.id} on date {date}")
    try:
        goals = Goal.objects.filter(
            user_id=user,
            start_date__lte=date,
            end_date__gte=date)

        if not goals.exists():
            logging.warning(f"No active goals found for user {user.id} on {date}")
            return []

        trends = []

        for goal in goals:

            if goal.start_date > goal.end_date:
                logging.warning(f"Invalid date range for goal {goal.goal_id}")
                continue

            # logging.info(f"Processing goal: {goal.goal_id}")

            total_days = (goal.end_date - goal.start_date).days  # total days

            if total_days <= 0:
                continue  # Skip goals with invalid or zero duration

            days_elapsed = calculate_days_elapsed(date, goal)

            # Special handling for day 0 (goal creation day)
            if days_elapsed == 0:
                trend_value = 0  # No progress expected on the first day
                trend = 'Neutral'
            else:
                try:
                    daily_target = Decimal(
                        goal.target_amount) / total_days if total_days > 0 else 0
                except (ZeroDivisionError, InvalidOperation):
                    logging.error(f"Invalid calculation for goal {goal.goal_id}")
                    continue
                expected_amount = daily_target * min(days_elapsed, total_days)

                try:
                    actual_amount = Decimal(goal.current_amount)
                except (TypeError, ValueError):
                    logging.error(
                        f"Invalid current_amount for goal {goal.goal_id}")
                    actual_amount = Decimal('0')

                trend_value = actual_amount - expected_amount
                trend = 'Positive' if trend_value >= 0 else 'Negative'

            # logging.info(f"Goal {goal.goal_id} trend: {trend} ({trend_value})")
            trends.append({'goal_id': goal.goal_id,
                           'trend': trend,
                           'trend_value': float(trend_value)
                           })

        # logging.info(f"Total trends calculated: {len(trends)}")
        return trends

    except Goal.DoesNotExist:
        # logging.error(f"Goal not found for user {user.id}")
        return []


def calculate_saving_progress(goal: Goal) -> Decimal:
    """Calculate the saving progress as a percentage of the current amount towards the target amount."""
    if goal.target_amount <= 0:
        return Decimal('0.00')  # Avoid division by zero

    progress_percentage = (goal.current_amount / goal.target_amount) * Decimal(
        '100.00')
    # 2 decimal places
    return progress_percentage.quantize(Decimal('0.01'),
                                        rounding=ROUND_CEILING)

def calculate_days_elapsed(date, goal):
    """ Calculate how many days have passed since the goal started"""
    days_elapsed = max(0, (
                date - goal.start_date).days)  # max to avoid negative days
    return days_elapsed

def calculate_avg_saving(user, date, goal_id):
    """
    Calculate the average daily saving been saved so far
    for the specified goal.
    #TODO: Average is now average saving per day. (So far) -- Not match goal view.
    """
    try:
        goal = Goal.objects.get(goal_id=goal_id, user_id=user)
        days_so_far = calculate_days_elapsed(date, goal)

        # Calculate average saving
        avg_saving = goal.current_amount / days_so_far if days_so_far > 0 else goal.current_amount
        # logging.info(f"Day so far: {days_so_far}, avg_saving: {avg_saving}, goal.current_amount: {goal.current_amount}, goal.target_amount: {goal.target_amount}")

        # 2 decimal places
        return avg_saving.quantize(Decimal('0.01'), rounding=ROUND_CEILING)

    except Goal.DoesNotExist:
        return Decimal('0.00').quantize(Decimal('0.01'),
                                        rounding=ROUND_CEILING)  # Goal not found

def update_current_amount(self, amount_saved):
    """Update current amount with a new saving input."""
    self.current_amount += Decimal(amount_saved)
    self.save()

def __str__(self):
    return f"{self.description}"

def calculate_min_saving(user, date, goal_id):
    """Calculate the minimum daily saving needed to reach the target amount."""
    try:
        goal = Goal.objects.get(goal_id=goal_id, user_id=user)

        # Calculate total days left until the end date
        total_days_left = calculate_days_remaining(user, date, goal_id)

        if total_days_left <= 0:
            return Decimal('0.00').quantize(Decimal('0.01'),
                                            rounding=ROUND_CEILING)  # Goal time has expired

        min_saving = goal.target_amount / total_days_left if total_days_left > 0 else Decimal('0.00')
        return min_saving.quantize(Decimal('0.01'),
                                   rounding=ROUND_CEILING)  # Round up to 2 decimal places

    except Goal.DoesNotExist:
        return Decimal('0.00').quantize(Decimal('0.01'),
                                        rounding=ROUND_CEILING)  # Goal not found


def rem_amount(goal):
    """Calculate remaining amount to reach target."""
    return max(Decimal('0.00'), goal.target_amount - goal.current_amount)


def calculate_saving_shortfall(user, date, goal_id):
    """Calculate the extra daily saving needed to meet the goal."""
    try:
        min_saving = calculate_min_saving(user, date, goal_id)

        saving_today = get_total_today_saving()

        # logging.info(f"min_saving: {min_saving}, saving_today: {saving_today}")

        # Calculate shortfall "extra saving needed per day"
        shortfall = min_saving - saving_today
        return max(Decimal('0.00'), shortfall).quantize(Decimal('0.01'),
                                                        rounding=ROUND_CEILING)  # Return 0 if no shortfall
    except Goal.DoesNotExist:
        return Decimal('0.00').quantize(Decimal('0.01'),
                                        rounding=ROUND_CEILING)  # Goal not found


def get_total_today_saving():
    """Get the total saving amount of today saving."""
    today_date = timezone.localtime(timezone.now()).date()
    goal_name = (
        IncomeExpense.objects.filter(
            description__startswith="Saving money to")
        .values_list('description', flat=True)
        .first()
        .replace("Saving money to ", "")
    )
    saving_today = (
            IncomeExpense.objects.filter(
                type='saving',
                goal__title=goal_name,
                date=today_date
            )
            .aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    )
    return saving_today


def get_all_goals(user):
    """
    Get all goals for the user.

    Args:
        user: The user for whom to retrieve the records.

    Returns:
        QuerySet: A list of Goal objects for the given user.
    """
    return Goal.objects.filter(user_id=user)

def calculate_burndown_chart(total_points, start_date, end_date,
                             completed_points_by_date):
    """
    Calculate burndown chart data using pandas.

    Args:
        total_points (float): Total story points at start
        start_date (datetime): Sprint start date
        end_date (datetime): Sprint end date
        completed_points_by_date (dict): Dictionary with dates as keys and completed points as values
            e.g. {'2024-01-01': 5, '2024-01-02': 3, ...}

    Returns:
        pandas.DataFrame: DataFrame with dates, ideal, and actual burndown lines
    """
    pass
    # # Create date range
    # date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    #
    # # Create DataFrame
    # df = pd.DataFrame(index=date_range)
    #
    # # Calculate ideal burndown line
    # total_days = len(date_range)
    # df['ideal'] = np.linspace(100, 0, total_days)
    #
    # # Calculate actual burndown
    # # df['completed'] = pd.Series(completed_points_by_date)
    # # df['completed'] = df['completed'].fillna(0).cumsum()
    # df['completed'] = pd.Series(completed_points_by_date).reindex(date_range, fill_value=0).cumsum()
    # df['remaining'] = 100 - df['completed']
    #
    # # Add formatted date column
    # df['date'] = df.index.strftime('%Y-%m-%d')
    #
    # # return df
    # return df[['date', 'ideal', 'remaining']].to_dict('records')

