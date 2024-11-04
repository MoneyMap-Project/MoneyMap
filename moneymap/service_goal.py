"""Service functions for the MoneyMap goal page."""

from datetime import timedelta, datetime
from django.db.models import Sum, F
from django.utils import timezone
from .models import Goal
from decimal import Decimal


import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def calculate_days_remaining(user, date, goal_id):
    """
    Calculate the days remaining to reach a specific goal for a user.

    Args:
        user: The user for whom to retrieve the records.
        date: The specific date for which to calculate the remaining days.
        goal_id: The ID of the specific goal for which to calculate remaining days.

    Returns:
        int: The number of days remaining to reach the specified goal, or None if the goal is not found or already past.
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
    goals = Goal.objects.filter(user_id=user, start_date__lte=date,
                                end_date__gte=date)
    trends = []

    for goal in goals:
        total_days = (goal.end_date - goal.start_date).days
        days_elapsed = (date - goal.start_date).days
        daily_target = goal.target_amount / total_days if total_days > 0 else 0
        expected_amount = daily_target * days_elapsed
        actual_amount = goal.current_amount
        trend_value = actual_amount - expected_amount

        trend = 'Positive' if trend_value >= 0 else 'Negative'
        trends.append({'goal_id': goal.goal_id, 'trend': trend,
                       'trend_value': trend_value})

    return trends


def calculate_saving_progress(goal: Goal) -> Decimal:
    """Calculate the saving progress as a percentage of the current amount towards the target amount."""
    if goal.target_amount <= 0:
        return Decimal('0.00')  # Avoid division by zero

    progress_percentage = (goal.current_amount / goal.target_amount) * Decimal(
        '100.00')
    # 2 decimal places
    return progress_percentage.quantize(Decimal('0.01'))


# def calculate_burndown_chart(user, date):
#     """
#     Calculate the burndown chart data for a user's goals.
#
#     Args:
#         user: The user for whom to retrieve the records.
#         date: The specific date for which to retrieve the records (datetime object).
#
#     Returns:
#         dict: Contains the following keys:
#             - 'ideal_line': List of ideal burndown points
#             - 'actual_line': List of actual progress points
#             - 'dates': List of dates for the x-axis
#             - 'total_points': Total story points at start
#             - 'remaining_points': Current remaining points
#             - 'completion_rate': Average daily completion rate
#     """
#     # Assuming we have a Goal model with fields:
#     # story_points, completed_points, start_date, end_date
#
#     # Get all active goals for the user
#     goals = Goal.objects.filter(
#         user=user,
#         start_date__lte=date,
#         end_date__gte=date,
#         is_active=True
#     )
#
#     if not goals.exists():
#         return {
#             'ideal_line': [],
#             'actual_line': [],
#             'dates': [],
#             'total_points': 0,
#             'remaining_points': 0,
#             'completion_rate': 0
#         }
#
#     # Calculate total story points
#     total_points = goals.aggregate(
#         total=Sum('story_points')
#     )['total'] or 0
#
#     # Calculate remaining points
#     remaining_points = goals.aggregate(
#         remaining=Sum(F('story_points') - F('completed_points'))
#     )['remaining'] or 0
#
#     # Get the earliest start date and latest end date
#     start_date = goals.order_by('start_date').first().start_date
#     end_date = goals.order_by('-end_date').first().end_date
#
#     # Calculate number of days in the sprint
#     total_days = (end_date - start_date).days + 1
#
#     # Generate dates list
#     dates = []
#     ideal_line = []
#     actual_line = []
#     current_date = start_date
#
#     # Calculate ideal daily decrease
#     if total_days > 1:
#         ideal_daily_decrease = total_points / (total_days - 1)
#     else:
#         ideal_daily_decrease = total_points
#
#     # Generate data points for each day
#     while current_date <= end_date:
#         dates.append(current_date.strftime('%Y-%m-%d'))
#
#         # Calculate ideal line
#         days_from_start = (current_date - start_date).days
#         ideal_points = max(0, total_points - (
#                     days_from_start * ideal_daily_decrease))
#         ideal_line.append(round(ideal_points, 2))
#
#         # Calculate actual line based on completed points up to this date
#         actual_points = goals.aggregate(
#             completed=Sum('completed_points',
#                           filter=F('updated_at__date__lte') == current_date)
#         )['completed'] or 0
#         actual_line.append(total_points - actual_points)
#
#         current_date += timedelta(days=1)
#
#     # Calculate average daily completion rate
#     if len(actual_line) > 1:
#         completion_rate = (actual_line[0] - actual_line[-1]) / len(actual_line)
#     else:
#         completion_rate = 0
#
#     return {
#         'ideal_line': ideal_line,
#         'actual_line': actual_line,
#         'dates': dates,
#         'total_points': total_points,
#         'remaining_points': remaining_points,
#         'completion_rate': round(completion_rate, 2)
#     }

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
    # Create date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # Create DataFrame
    df = pd.DataFrame(index=date_range)

    # Calculate ideal burndown line
    total_days = len(date_range)
    df['ideal'] = np.linspace(100, 0, total_days)

    # Calculate actual burndown
    # df['completed'] = pd.Series(completed_points_by_date)
    # df['completed'] = df['completed'].fillna(0).cumsum()
    df['completed'] = pd.Series(completed_points_by_date).reindex(date_range, fill_value=0).cumsum()
    df['remaining'] = 100 - df['completed']

    # Add formatted date column
    df['date'] = df.index.strftime('%Y-%m-%d')

    # return df
    return df[['date', 'ideal', 'remaining']].to_dict('records')

def calculate_avg_saving(user, date):
    """
    Calculate the average saving for the user.

    Args:
        user: The user for whom to retrieve the records.
        date: The specific date for which to retrieve the records.

    Returns:
        QuerySet: A list of Goal objects for the given user.
    """
    pass

def calculate_min_saving(user, date):
    """
    Calculate the minimum saving for the user.

    Args:
        user: The user for whom to retrieve the records.
        date: The specific date for which to retrieve the records.

    Returns:
        QuerySet: A list of Goal objects for the given user.
    """
    pass

def calculate_saving_shortfall(user, date):
    """
    Calculate extra needed daily to meet the goal for the user.

    Args:
        user: The user for whom to retrieve the records.
        date: The specific date for which to retrieve the records.

    Returns:
        QuerySet: A list of Goal objects for the given user.
    """
    pass

def get_all_goals(user):
    """
    Get all goals for the user.

    Args:
        user: The user for whom to retrieve the records.

    Returns:
        QuerySet: A list of Goal objects for the given user.
    """
    return Goal.objects.filter(user_id=user)
