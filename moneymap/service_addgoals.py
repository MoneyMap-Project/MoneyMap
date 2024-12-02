from django.utils import timezone
from .service_detailgoals import get_total_today_saving
from .models import Goal, IncomeExpense
from django.db.models import Sum, F
from decimal import Decimal


def calculate_days_remaining(end_date):
    """Calculate the days remaining until the goal deadline."""
    return max((end_date - timezone.now().date()).days, 0)

def calculate_average_saving(current_amount, current_total_days):
    """Calculate the average saving per day to reach the goal."""
    return current_amount / current_total_days if current_total_days > 0 else 0

def calculate_minimum_saving(target_amount, current_amount, days_remaining):
    """Calculate the minimum saving required each day to reach the goal."""
    return (target_amount - current_amount) / days_remaining if days_remaining > 0 else 0

def calculate_progress_percentage(current_amount, target_amount):
    """Calculate the progress percentage towards the goal."""
    return (current_amount / target_amount) * 100 if target_amount > 0 else 0

def get_goals_data(user_goals):
    """Process and return a list of goal data dictionaries for the template."""
    goals_data = []
    local_time = timezone.localtime(timezone.now())
    date = local_time.date()

    for goal in user_goals:
        days_remaining = calculate_days_remaining(goal.end_date)
        min_saving = calculate_minimum_saving(goal.target_amount, goal.current_amount, days_remaining)
        progress_percentage = calculate_progress_percentage(goal.current_amount, goal.target_amount)

        total_days = (goal.end_date - goal.start_date).days + 1
        current_total_days = (date - goal.start_date).days + 1
        avg_saving = calculate_average_saving(goal.current_amount,
                                              current_total_days)
        daily_target = goal.target_amount / total_days if total_days > 0 else 0
        total_saving_today = get_total_today_saving(goal.goal_id)

        trend_value = daily_target - total_saving_today
        trend = 'Positive' if trend_value <= 0 else 'Negative'

        goals_data.append({
            'id': goal.goal_id,
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
