from django.utils import timezone
from django.contrib import messages
from decimal import Decimal
from django.shortcuts import redirect
from .models import Goal, IncomeExpense


def validate_goal_end_dates(goals, request):
    """
    Validate that the goals' end dates are not in the past.
    """
    local_time = timezone.localtime(timezone.now())
    current_date = local_time.date()
    invalid_goals = goals.filter(end_date__lt=current_date)

    if invalid_goals.exists():
        # Collect the titles of invalid goals for the error message
        invalid_goal_titles = ', '.join(
            invalid_goals.values_list('title', flat=True))
        messages.error(
            request,
            f"The following goals have expired and cannot accept savings: {invalid_goal_titles}.",
            extra_tags='expired_goal'  # Specific tag for this error
        )
        return redirect('moneymap:add_money_goals')

    return None  # Return None if all goals are valid

def validate_amount(amount, request):
    """Validate the amount to ensure it is a positive number greater than zero."""
    amount_decimal = Decimal(amount)
    # Check if the amount is zero or negative
    if amount_decimal <= 0:
        # Add an error message with a specific tag
        messages.error(
            request,
            "Amount must be a positive number greater than zero.",
            extra_tags='amount'  # Specific tag for this error
        )
        return redirect('moneymap:add_money_goals')
    return amount_decimal

def get_goals(user, distribute_evenly, selected_goals, select_custom_goals):
    """Retrieve the goals based on the user's selection."""
    if distribute_evenly == 'on' and select_custom_goals is None:
        # Retrieve all goals for the user
        return Goal.objects.filter(user_id=user)
    elif distribute_evenly is None and select_custom_goals == 'on':
        # Retrieve selected goals
        return Goal.objects.filter(goal_id__in=selected_goals, user_id=user)
    else:
        # Return no goals if neither condition is met
        return Goal.objects.none()

def check_goals_availability(goals, amount_decimal, request):
    """Check if there is enough space in the selected goals for the saving amount."""
    total_available_space = 0
    for goal in goals:
        available_space = goal.target_amount - goal.current_amount
        total_available_space += available_space

    if amount_decimal > total_available_space:
        # Add an error message with a specific tag
        messages.error(
            request,
            "Saving amount exceeds the target amount of the selected goals.",
            extra_tags='saving'
        )
        return redirect('moneymap:add_money_goals')
    return None  # Return None if everything is fine


def distribute_savings(goals, amount_decimal, add_to_income_expense, parsed_date, user, request):
    """Distribute the saving amount evenly among selected goals."""
    amount_per_goal = amount_decimal / len(goals)

    for goal in goals:
        available_space = goal.target_amount - goal.current_amount
        if amount_per_goal > available_space:
            # Add an error message with a specific tag
            messages.error(
                request,
                f"Saving amount for {goal.title} exceeds its available space.",
                extra_tags='goal'  # Specific tag for this error
            )
            # Redirect back to the add_money_goals page
            return redirect('moneymap:add_money_goals')

        # Update the goal's current amount
        goal.current_amount += amount_per_goal
        goal.save()

        # create an IncomeExpense record
        if add_to_income_expense:
            income_expense = IncomeExpense.objects.create(
                user_id=user,
                type='saving',
                amount=amount_per_goal,
                date=parsed_date,
                description=f'Saving money to {goal.title}',
                saved_to_income_expense=True,
            )
        else:
            income_expense = IncomeExpense.objects.create(
                user_id=user,
                type='saving',
                amount=amount_per_goal,
                date=parsed_date,
                description=f'Saving money to {goal.title}',
                saved_to_income_expense=False,
            )
        income_expense.goal.add(goal)

    return None  # Return None if everything is fine


def handle_goal_error(request, error_message, redirect_url, tag):
    """Helper function to handle goal-related errors."""
    messages.error(request, error_message, extra_tags=tag)
    return redirect(redirect_url)
