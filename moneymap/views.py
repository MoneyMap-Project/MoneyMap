"""
Views for the MoneyMap application.
This module contains views related to managing income and expenses,
displaying financial reports, and handling user interactions.
"""
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.generic import TemplateView, DetailView
from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin

from .service_addgoals import (
    calculate_days_remaining,
    calculate_average_saving,
    calculate_minimum_saving,
    get_goals_data
)
from .service_addsavingmoney import (
    validate_goal_end_dates,
    validate_amount,
    get_goals,
    check_goals_availability,
    distribute_savings,
    handle_goal_error,
)
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
from .service_detailgoals import (
    # calculate_days_remaining,
    calculate_trend,
    calculate_saving_progress,
    # calculate_avg_saving,
    # calculate_min_saving,
    calculate_saving_shortfall,
    get_all_goals, get_all_saving_specific_goal, get_current_total_days
)
from .models import IncomeExpense, Goal, Tag

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
                saved_to_income_expense=True,
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
    """Delete an IncomeExpense object and update the related goal if necessary."""

    # Retrieve the IncomeExpense object or return 404 if not found
    income_expense = get_object_or_404(IncomeExpense,
                                       IncomeExpense_id=income_expense_id,
                                       user_id=request.user)

    # Check if the record type is 'saving'
    if income_expense.type == 'saving':
        # Retrieve the related goal
        goal = Goal.objects.filter(
            user_id=request.user,
            title=income_expense.description.split(" to ")[-1]  # the description follows the format "Saving money to <goal_title>"
        ).first()

        # Update the goal's current amount
        if goal:
            goal.current_amount -= Decimal(income_expense.amount)
            if goal.current_amount < 0:
                goal.current_amount = Decimal('0.00')  # Ensure the amount does not go below zero
            goal.save()

    # Delete the IncomeExpense object
    income_expense.delete()

    # Add a success message
    messages.success(request, 'Income/Expense record successfully deleted.')

    # Redirect back to the income and expenses view
    return redirect('moneymap:income-expenses')

class GoalView(LoginRequiredMixin, TemplateView):
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

        return context


class MoneyFlowView(LoginRequiredMixin, View):
    """
    View to handle the Money Flow page functionality.

    This view provides methods to display the money flow form (GET request) and
    handle form submissions (POST request). It supports managing session data
    for temporary input storage, creating IncomeExpense objects, and associating
    tags with the created records.
    """
    def get(self, request):
        """
        Handle GET requests for the money flow form.

        This method retrieves user-specific tags and any previously saved
        session data (description, amount, and money type). It renders the
        money flow form with the retrieved context.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            HttpResponse: Rendered money flow form with context data.
        """
        tags = Tag.objects.filter(user_id=request.user)

        description = request.session.get('description', '')
        amount = request.session.get('amount', '')
        money_type = request.session.get('money_type', '')

        moneytype = request.GET.get('moneytype', 'income')

        return render(request, 'moneymap/money-flow.html',
                      context={
                          "tags": tags,
                          "description": description,
                          "amount": amount,
                          "money_type": money_type,
                          "moneytype": moneytype
                      })

    def post(self, request):
        """
        Handle POST requests to process the money flow form.

        This method processes the form data submitted by the user. It validates
        the input, creates an `IncomeExpense` object, associates selected tags,
        and clears session data upon successful form submission. If errors
        occur, it re-renders the form with the entered data and tags.

        Args:
            request (HttpRequest): The HTTP request object containing form data.

        Returns:
            HttpResponse: A redirect to the income-expenses page on success,
                          or re-renders the form with errors otherwise.
        """
        selected_type = request.POST.get('money_type')
        amount = request.POST.get('amount')
        description = request.POST.get('description')

        try:
            amount_decimal = float(amount)

            # Create and save the IncomeExpense object
            new_income_expense = IncomeExpense.objects.create(
                user_id=request.user,
                saved_to_income_expense=True,
                type=selected_type,
                amount=amount_decimal,
                date=timezone.now(),
                description=description,
            )

            selected_tag_id = request.POST.get('selected_tag')
            if selected_tag_id:
                try:
                    tag = Tag.objects.get(id=selected_tag_id, user_id=request.user)
                    new_income_expense.tags.add(tag)
                except Tag.DoesNotExist:
                    logging.warning("Selected tag %s does not exist or doesn't belong to user", selected_tag_id)

            # Clear session data
            request.session.pop('description', None)
            request.session.pop('amount', None)
            request.session.pop('money_type', None)

            return redirect('moneymap:income-expenses')

        except ValueError:
            logging.error("Invalid amount entered. Please enter a valid number.")
        except Exception as specific_error:
            logging.exception("An unexpected error occurred: %s", specific_error)

        tags = Tag.objects.filter(user_id=request.user)
        return render(request, 'moneymap/money-flow.html', {
            "tags": tags,
            "description": description,
            "amount": amount,
            "money_type": selected_type
        })


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
            saved_to_income_expense=True,
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


class AddSavingMoney(LoginRequiredMixin, TemplateView):
    """View to add saving records associated with goals that user want."""
    template_name = 'moneymap/add-money-goals.html'

    def get(self, request):
        """Render the Add Money form with the user's goals."""
        if request.user.is_authenticated:
            # Retrieve the user's goals
            user_goals = Goal.objects.filter(user_id=request.user)
            return render(request, self.template_name, {'goals': user_goals})
        # Redirect to login if the user is not authenticated
        return redirect('login')

    def post(self, request):
        """Handle the submitted form data for adding money."""
        local_time = timezone.localtime(timezone.now())

        amount = request.POST.get('goal_amount')
        date = str(local_time.date())
        distribute_evenly = request.POST.get('distribute_evenly')
        select_custom_goals = request.POST.get('select_custom_goals')
        selected_goals = request.POST.getlist('selected_goals[]')
        add_to_income_expense = request.POST.get('add_income_expense')

        try:
            # Validate amount
            amount_decimal = validate_amount(amount, request)

            # Validate and parse date
            if not date:
                raise ValueError("Date is required.")
            parsed_date = datetime.strptime(date, '%Y-%m-%d').date()

            goals = get_goals(request.user, distribute_evenly, selected_goals, select_custom_goals)

            if not goals.exists():
                return handle_goal_error(request, "No goals selected or you have no goals.",
                                         'moneymap:add_money_goals',
                                         'no_goals_error')

            # Validate goal end dates
            redirect_url = validate_goal_end_dates(goals, request)
            if redirect_url:
                return redirect_url

            # Check if the saving amount exceeds the available space for the selected goals
            redirect_url = check_goals_availability(goals, amount_decimal, request)
            if redirect_url:
                return redirect_url

            # Distribute savings to goals
            params = {
                'goals': goals,
                'amount_decimal': amount_decimal,
                'add_to_income_expense': add_to_income_expense,
                'parsed_date': parsed_date,
                'user': request.user,
                'request': request
            }
            redirect_url = distribute_savings(params)
            if redirect_url:
                return redirect_url

            # Redirect to the goals or income-expenses page
            return redirect('moneymap:goals')

        except ValueError as e:
            logging.error(str(e))
            return render(request, self.template_name, {'error': str(e)})
        except Exception as specific_error:
            logging.exception("An unexpected error occurred: %s", specific_error)
            return render(request, self.template_name, {'error': 'An unexpected error occurred.'})


class AddGoals(LoginRequiredMixin, TemplateView):
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
            # print(f"Converted target amount: {target_amount_decimal}")

            # Create and save a new Goal object
            Goal.objects.create(
                user_id=request.user,
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date,
                target_amount=target_amount_decimal,
                current_amount=0,
            )
            logger.debug(request, 'Income/Expense recorded successfully!')
            return redirect('moneymap:goals')
        except ValueError:
            logging.error("Invalid target amount entered. Please enter a valid number.")
            return render(request, 'moneymap/add_goals.html', {'error': 'Invalid target amount entered.'})
        except Exception as specific_error:
            logging.exception("An unexpected error occurred: %s", specific_error)
            return render(request, 'moneymap/add_goals.html', {'error': 'An unexpected error occurred.'})


class BaseTagView(View):
    """
    A base view for handling tag-related functionality, such as saving form data
    in the session for later use.
    """
    @staticmethod
    def save_session_data(request):
        """
        Helper method to save and return form data (description, amount, money_type)
        in the session.

        Args:
            request (HttpRequest): The incoming HTTP request object.

        Returns:
            tuple: A tuple containing the description, amount, and money_type.
        """
        description = request.POST.get('description', '')
        amount = request.POST.get('amount', '')
        money_type = request.POST.get('money_type', '')

        request.session['description'] = description
        request.session['amount'] = amount
        request.session['money_type'] = money_type

        return description, amount, money_type


class AddTagView(BaseTagView):
    """
    A view for adding a new tag. It handles the POST request to create a new tag
    and validates the tag name before saving it.
    """

    def post(self, request):
        """
        Handles the POST request to create a new tag. It validates the tag name
        (ensuring it's not empty, not too long, and does not already exist)
        and saves it to the database. Displays appropriate messages to the user
        for success or errors.

        Args:
            request (HttpRequest): The incoming HTTP request object.

        Returns:
            HttpResponse: A redirect to the 'money-flow' page after processing the request.
        """
        tag_name = request.POST.get('tag_name').strip()
        self.save_session_data(request)

        if not tag_name:
            messages.error(request, "Tag name cannot be empty.")
        elif len(tag_name) > 100:
            messages.error(request, "Tag name cannot be longer than 100 characters.")
        elif Tag.objects.filter(name=tag_name, user_id=request.user).exists():
            messages.error(request, "Tag name already exists.")
        else:
            new_tag = Tag.objects.create(
                name=tag_name,
                user_id=request.user
            )
            new_tag.save()
            messages.success(request, "Tag added successfully.")

        return redirect('moneymap:money-flow')


class DeleteTagView(BaseTagView):
    """
    A view for deleting an existing tag. It handles the POST request to remove
    a tag by its ID from the database.
    """
    def post(self, request):
        """
        Handles the POST request to delete a tag. It deletes the tag with the
        provided ID from the database.

        Args:
            request (HttpRequest): The incoming HTTP request object.

        Returns:
            HttpResponse: A redirect to the 'money-flow' page after deleting the tag.
        """
        tag_id = request.POST.get('tag_id')
        self.save_session_data(request)

        if tag_id:
            Tag.objects.filter(id=tag_id).delete()

        return redirect('moneymap:money-flow')


class GoalsDetailView(LoginRequiredMixin, DetailView):
    """Goal Report for a specific date."""
    model = Goal
    template_name = 'moneymap/goals-detail.html'
    context_object_name = 'goal'

    def get(self, request, *args, **kwargs):
        goal_id = kwargs.get('pk')
        selected_goal = get_object_or_404(self.get_queryset(), pk=goal_id)

        # Set the object for use in the template
        self.object = selected_goal
        context = self.get_context_data(goal=self.object, user=request.user)  # Pass the single goal instance
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('login')

        context = super().get_context_data(**kwargs)
        goal = self.object  # `self.object` is set by DetailView

        # user = self.request.user
        current_date = timezone.localtime(timezone.now()).date()  # Get today's date

        # Calculate the remaining days for the goal
        remaining_days = calculate_days_remaining(goal.end_date)

        # Calculate the saving trends
        trends = calculate_trend(goal.goal_id)
        # only show the trend for the current goal
        trend_for_goal = next(
            (trend for trend in trends if trend['goal_id'] == goal.goal_id),
            None)
        trend_status = trend_for_goal[
            'trend'] if trend_for_goal else "No trend data"

        # -- For the goal progress CARD --
        current_amount = goal.current_amount
        target_amount = goal.target_amount
        saving_progress = calculate_saving_progress(goal)
        current_total_days = get_current_total_days(goal, current_date)

        avg_saving = calculate_average_saving(goal.current_amount, current_total_days)
        min_saving = round(calculate_minimum_saving(goal.target_amount, goal.current_amount, remaining_days), 2)
        saving_shortfall = calculate_saving_shortfall(goal.goal_id)

        # -- For the burndown chart --
        start_date = goal.start_date
        end_date = goal.end_date

        # Generate dates for the burndown chart
        total_days = (end_date - start_date).days # Total days between start and end date
        date_labels = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                       for i in range(total_days + 1)]

        # logging.debug(f"Date labels: {date_labels}")

        # Ideal savings calculation
        ideal_savings = [
            goal.target_amount * (Decimal('1') - Decimal(i) / Decimal(total_days))
            for i in range(total_days + 1)
        ]

        # Actual savings
        actual_saving = get_all_saving_specific_goal(goal.title)
        # logging.debug(f"actual saving: {actual_saving}")

        # Aggregate and align actual savings
        aggregated_savings = aggregate_savings_by_date(actual_saving)  # Aggregate by date
        aligned_actual_savings = align_savings_with_labels(date_labels, aggregated_savings)  # Align with labels

        # logging.debug(f"Aggregated savings: {aligned_actual_savings}")
        # if save day, amount is combine all together

        # Convert data to floats for JSON serialization
        ideal_but_float = [float(x) for x in ideal_savings]
        actual_but_float = aligned_actual_savings

        # logging.debug(f"i savings: {[float(x) for x in ideal_savings]}")
        # logging.debug(f"a savings: {[float(x) for x in actual_savings]}")
        context['start_date'] = goal.start_date.strftime("%d %B %Y").lstrip("0")
        context['end_date'] = goal.end_date.strftime("%d %B %Y").lstrip("0")
        context['remaining_day'] = remaining_days if remaining_days is not None else "Goal not found"
        context['trends'] = trend_status
        context['current_amount'] = current_amount
        context['target_amount'] = target_amount
        context['saving_progress'] = saving_progress
        context['avg_saving'] = avg_saving
        context['min_saving'] = min_saving
        context['saving_shortfall'] = saving_shortfall
        context['goal'] = self.get_object()
        context['goal_id'] = goal.goal_id

        context["chart_labels"] = json.dumps(date_labels)
        context["chart_ideal_data"] = ideal_but_float
        context["chart_actual_data"] = actual_but_float

        return context


def aggregate_savings_by_date(actual_saving):
    # Create a dictionary to store total savings for each date
    savings_by_date = {}

    for entry in actual_saving:
        date = entry['date']
        amount = entry['__amount']
        if date in savings_by_date:
            savings_by_date[date] += amount
        else:
            savings_by_date[date] = amount

    return savings_by_date

def align_savings_with_labels(chart_labels, savings_by_date):
    aligned_savings = []

    for label in chart_labels:
        date = datetime.strptime(label, "%Y-%m-%d").date()
        aligned_savings.append(float(savings_by_date.get(date, Decimal('0.00'))))  # Default to 0 if no data

    return aligned_savings

@login_required
def delete_goal(request, goal_id):
    """Delete a goal object."""
    if request.method == 'POST':
        goal = get_object_or_404(Goal, goal_id=goal_id)
        # delete all transactions related to that goal
        IncomeExpense.objects.filter(description__contains=goal.title).delete()
        # delete the goal
        goal.delete()
        messages.success(request, 'Goal successfully deleted.')
        # Redirect to the goals page
        return redirect('moneymap:goals')
    return HttpResponseForbidden('Invalid request method.')
