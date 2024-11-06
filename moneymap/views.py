"""
Views for the MoneyMap application.
This module contains views related to managing income and expenses,
displaying financial reports, and handling user interactions.
"""
from datetime import date
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

from .service_addgoals import get_goals_data, calculate_trend
from .service import (
    calculate_balance,
    calculate_balance_last_7_days,
    sum_income,
    sum_expense,
    sum_income_by_month,
    sum_expense_by_month,
    calculate_income_expense_percentage,
    get_income_expense_by_day,
)
from .models import IncomeExpense, Goal

# logger

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    """Render the home page."""
    template_name = 'moneymap/home.html'


class IncomeAndExpensesView(TemplateView):
    """View for displaying today's income and expenses."""
    template_name = 'moneymap/income-expenses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        local_time = timezone.localtime(timezone.now())
        today = local_time.date()

        if self.request.user.is_authenticated:
            # Retrieve income/expense records for today
            income_expenses_today = IncomeExpense.objects.filter(
                user_id=self.request.user,
                date=today
            ).order_by('date')

            # Use the function to calculate balance for the last 7 days
            context['income_expense_with_balance_last_7_days'] = calculate_balance_last_7_days(
                self.request.user, today)

            # Calculate today's balance separately
            context['income_expense_with_balance_today'] = calculate_balance(
                income_expenses_today)

            # Indicate if there's data for today
            context['has_data'] = bool(context['income_expense_with_balance_today'])
            context['user_id_display'] = self.request.user.username
        else:
            # If user is not authenticated, set default context values
            context['income_expense_with_balance_today'] = []
            context['income_expense_with_balance_last_7_days'] = []
            context['has_data'] = False
            context['user_id_display'] = 'guest'

        return context


@login_required
def delete_income_expense(request, income_expense_id):
    """For delete an IncomeExpense object"""

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


class GoalView(TemplateView):
    """View for the goals page."""
    template_name = 'moneymap/goals.html'

    def get(self, request, *args, **kwargs):
        """Retrieve and display the goals for the current user."""
        # Call get_context_data to prepare context with goals data
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """Retrieve and prepare context data for the goals page."""
        context = super().get_context_data(**kwargs)
        
        # Retrieve goals for the current user
        user_goals = Goal.objects.filter(user_id=self.request.user)
        
        # Get the processed goals data from the service function
        context['goals_data'] = get_goals_data(user_goals)

        # Calculate trend data for each goal
        date = timezone.now().date()
        context['goal_trends'] = calculate_trend(self.request.user, date)
        
        return context
    

@login_required
def delete_goal(request, goal_id):
    """For delete a Goal object"""

    # Retrieve the Goal object or return 404 if not found
    goal = get_object_or_404(Goal, goal_id=goal_id, user_id=request.user)

    # Delete the object
    goal.delete()

    # Add a success message
    messages.success(request, 'Goal successfully deleted.')

    # Redirect back to the goals view
    return redirect('moneymap:goals')

class MoneyFlowView(LoginRequiredMixin, View):
    """
    After clicking the `Income and Expense` button,
    this view will be called.
    """

    def get(self, request):
        """Render the money flow form."""
        return render(request, 'moneymap/money-flow.html')

    def post(self, request):
        """Handle the submitted form data."""
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
            # logger.debug(request, 'Income/Expense recorded successfully!')
            return redirect('moneymap:income-expenses')
        except ValueError:
            logging.error("Invalid amount entered. Please enter a valid number.")
        except Exception as specific_error:
            logging.exception("An unexpected error occurred: %s", specific_error)

        # Render the form again with any errors (optional)
        return render(request, 'moneymap/money-flow.html')


class IncomeAndExpensesDetailView(LoginRequiredMixin, TemplateView):
    """Income and Expense Report for a specific date."""
    template_name = 'moneymap/income-expense-detail.html'

    def get(self, request, *args, **kwargs):
        # Convert the date string to a datetime object
        date_str = kwargs.get('date')
        try:
            selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            logger.error("Invalid date format.")
            return redirect('moneymap:income-expenses')

        # Retrieve IncomeExpense records for the selected date and the logged-in user
        income_expenses = IncomeExpense.objects.filter(
            user_id=request.user,
            date=selected_date
        ).order_by('date')

        # Prepare the context data
        context = self.get_context_data(income_expenses=income_expenses, selected_date=selected_date)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        income_expenses = kwargs.get('income_expenses')
        selected_date = kwargs.get('selected_date')

        if income_expenses.exists():
            income_expense_with_balance = calculate_balance(income_expenses)
            context['latest_balance'] = income_expense_with_balance[-1]['balance']
            context['day_income'] = sum_income(self.request.user, selected_date)
            context['day_expense'] = sum_expense(self.request.user, selected_date)
            context['has_data'] = True
        else:
            income_expense_with_balance = None
            context['latest_balance'] = 0
            context['day_income'] = 0
            context['day_expense'] = 0
            context['has_data'] = False

        # Monthly income and expense calculations
        month_income = sum_income_by_month(self.request.user, selected_date.month)
        month_expense = sum_expense_by_month(self.request.user, selected_date.month)
        context['month_income'] = month_income
        context['month_expense'] = month_expense
        context['month_balance'] = month_income - month_expense

        # Income and expense percentages
        percentages = calculate_income_expense_percentage(month_income, month_expense)
        context['income_percent'] = percentages['income_percent']
        context['expense_percent'] = percentages['expense_percent']

        # Additional context
        context['income_expense_with_balance'] = income_expense_with_balance
        context['selected_date'] = selected_date

        return context


class HistoryView(LoginRequiredMixin, View):
    """View showing income and expense history, grouped by date."""

    def get(self, request):
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

            # Filter the date from the range that user selected
            dates = IncomeExpense.objects.filter(
                user_id=request.user,
                date__range=[start_date, end_date]
            ).dates('date', 'day')
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


class AddMoney(TemplateView):
    template_name = 'moneymap/add-money-goals.html'

    
class AddGoals(TemplateView):
    template_name = 'moneymap/add_goals.html'

    def get(self, request):
        """Render the money flow form."""
        return render(request, 'moneymap/add_goals.html')

    def post(self, request):
        """Handle the submitted form data."""
        title = request.POST.get('goal_title')
        description = request.POST.get('goal_description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        target_amount = request.POST.get('target_amount')

        try:
            target_amount_decimal = float(target_amount)
            print(f"Converted target amount: {target_amount_decimal}")

            # Create and save a new Goal object
            new_goal = Goal.objects.create(
                user_id=request.user,
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date,
                target_amount=target_amount_decimal,
                current_amount=0,
            )
            print(f"New Goal object created: {new_goal}")
            # logger.debug(request, 'Income/Expense recorded successfully!')
            return redirect('moneymap:goals')
        except ValueError:
            logging.error("Invalid target amount entered. Please enter a valid number.")
            return render(request, 'moneymap/add_goals.html', {'error': 'Invalid target amount entered.'})
        except Exception as specific_error:
            logging.exception("An unexpected error occurred: %s", specific_error)
            return render(request, 'moneymap/add_goals.html', {'error': 'An unexpected error occurred.'})


class GoalsDetail(TemplateView):
    template_name = 'moneymap/goals-detail.html'
