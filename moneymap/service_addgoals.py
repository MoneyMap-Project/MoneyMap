from datetime import date
from django.utils import timezone
from .models import Goal

def calculate_days_remaining(end_date):
    """Calculate the days remaining until the goal deadline."""
    return max((end_date - timezone.now().date()).days, 0)

def calculate_average_saving(target_amount, total_days):
    """Calculate the average saving per day to reach the goal."""
    return target_amount / total_days if total_days > 0 else 0

def calculate_minimum_saving(target_amount, current_amount, days_remaining):
    """Calculate the minimum saving required each day to reach the goal."""
    return (target_amount - current_amount) / days_remaining if days_remaining > 0 else 0

def calculate_progress_percentage(current_amount, target_amount):
    """Calculate the progress percentage towards the goal."""
    return (current_amount / target_amount) * 100 if target_amount > 0 else 0

def get_goals_data(user_goals, date):
    """Process and return a list of goal data dictionaries for the template."""
    goals_data = []

    for goal in user_goals:
        days_remaining = calculate_days_remaining(goal.end_date)
        avg_saving = calculate_average_saving(goal.target_amount, goal.total_days)
        min_saving = calculate_minimum_saving(goal.target_amount, goal.current_amount, days_remaining)
        progress_percentage = calculate_progress_percentage(goal.current_amount, goal.target_amount)

        total_days = (goal.end_date - goal.start_date).days
        days_elapsed = (date - goal.start_date).days
        daily_target = goal.target_amount / total_days if total_days > 0 else 0
        expected_amount = daily_target * days_elapsed
        actual_amount = goal.current_amount
        trend_value = actual_amount - expected_amount

        trend = 'Positive' if trend_value >= 0 else 'Negative'

        goals_data.append({
            'title': goal.title,
            'description': goal.description,
            'deadline': goal.end_date,
            'average_saving': avg_saving,
            'minimum_saving': min_saving,
            'progress': f"{goal.current_amount} Baht / {goal.target_amount} Baht",
            'days_remaining': days_remaining,
            'progress_percentage': progress_percentage,
            'trend': trend,
            'trend_value': trend_value

        })

    return goals_data

# def calculate_trend(user, date):
#     """
#     Calculate the trend for each goal for the given user and date.

#     Args:
#         user: The user for whom to retrieve the records.
#         date: The specific date for which to retrieve the records.

#     Returns:
#         list: A list of dictionaries containing goal_id and their respective trends.
#     """
#     goals = Goal.objects.filter(user_id=user, start_date__lte=date, end_date__gte=date)
#     trends = []

#     for goal in goals:
#         total_days = (goal.end_date - goal.start_date).days
#         days_elapsed = (date - goal.start_date).days
#         daily_target = goal.target_amount / total_days if total_days > 0 else 0
#         expected_amount = daily_target * days_elapsed
#         actual_amount = goal.current_amount
#         trend_value = actual_amount - expected_amount

#         trend = 'Positive' if trend_value >= 0 else 'Negative'
#         trends.append({
#             'goal_id': goal.goal_id,
#             'trend': trend,
#             'trend_value': trend_value
#         })

#     return trends