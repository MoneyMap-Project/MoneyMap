"""
Unit tests for the IncomeExpense model and related services/views in the moneymap application.
"""
from datetime import date
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse
from moneymap.models import IncomeExpense
from moneymap.service import (
    calculate_balance, get_income_expense_by_day,
    calculate_balance_last_7_days,
    sum_income, sum_expense, sum_income_by_month, sum_expense_by_month,
    calculate_income_expense_percentage
)


class IncomeExpenseModelTests(TestCase):
    """Test the IncomeExpense model."""

    def test_create_income_expense(self):
        """Test creating an income expense object."""
        # Create a new user
        user = User.objects.create_user(username='testuser',
                                        password='testpassword')
        user.save()

        # Capture the current time before creating the income expense object
        now = timezone.now()

        # Create a new income expense object
        income_expense = IncomeExpense.objects.create(
            user_id=user,
            type='Income',
            amount=100.00,
            date=now,
            description='Test income expense object',
            saved_to_income_expense=True
        )
        income_expense.save()

        # Check if the income expense object was created successfully
        self.assertEqual(income_expense.user_id, user)
        self.assertEqual(income_expense.type, 'Income')
        self.assertEqual(income_expense.amount, 100.00)
        self.assertEqual(income_expense.date,
                         now)  # Compare with the captured time
        self.assertEqual(income_expense.description,
                         'Test income expense object')
        self.assertEqual(income_expense.saved_to_income_expense, True)

    def test_save_income_expense_view(self):
        """Test saving an income expense object in database."""

        # Create a new user
        user = User.objects.create_user(username='testuser',
                                        password='testpassword')
        user.save()

        # Capture the current time before creating the income expense object
        now = timezone.now()

        # Create a new income expense object
        income_expense = IncomeExpense.objects.create(
            user_id=user,
            type='Income',
            amount=100.00,
            date=now,
            description='Test income expense object',
            saved_to_income_expense=True
        )
        income_expense.save()

        # Check if the income expense object was saved successfully
        self.assertTrue(income_expense.pk)
        self.assertTrue(income_expense.user_id)
        self.assertTrue(income_expense.type)
        self.assertTrue(income_expense.amount)
        self.assertTrue(income_expense.date)
        self.assertTrue(income_expense.description)
        self.assertTrue(income_expense.saved_to_income_expense)


class IncomeExpenseServiceTests(TestCase):
    """Test the calculate_balance utility function."""

    def test_calculate_balance(self):
        """Test if the balance for today is calculated correctly, line by line."""

        user = User.objects.create_user(username='testuser', password='testpassword')
        user.save()

        today = timezone.localtime(timezone.now()).date()

        # Create multiple income and expense objects for today
        income_expense1 = IncomeExpense.objects.create(
            user_id=user,
            type='Income',
            amount=200.00,
            date=today,
            description='Income 1',
            saved_to_income_expense=True
        )

        income_expense2 = IncomeExpense.objects.create(
            user_id=user,
            type='Expense',
            amount=50.00,
            date=today,
            description='Expense 1',
            saved_to_income_expense=True
        )

        income_expense3 = IncomeExpense.objects.create(
            user_id=user,
            type='Income',
            amount=100.00,
            date=today,
            description='Income 2',
            saved_to_income_expense=True
        )

        income_expenses_today = IncomeExpense.objects.filter(user_id=user, date=today).order_by('date')
        income_expense_with_balance = calculate_balance(income_expenses_today)

        self.assertEqual(income_expense_with_balance[0]['balance'], 200.00)  # First balance
        self.assertEqual(income_expense_with_balance[1]['balance'], 150.00)  # After expense
        self.assertEqual(income_expense_with_balance[2]['balance'], 250.00)  # Final balance after second income

        self.assertEqual(income_expense1.amount, 200.00)
        self.assertEqual(income_expense2.amount, 50.00)
        self.assertEqual(income_expense3.amount, 100.00)


class IncomeExpenseViewsTests(TestCase):
    """Test the views in the income and expense view."""

    def setUp(self):
        # Set up a user for authentication
        self.user = User.objects.create_user(
            username='testuser', password='password123'
        )
        self.client.login(username='testuser', password='password123')

        # Create test income and expense records
        self.income1 = IncomeExpense.objects.create(
            user_id=self.user,
            type='Income',
            amount=1000.00,
            date=date(2024, 10, 1),
            description='Salary'
        )
        self.income2 = IncomeExpense.objects.create(
            user_id=self.user,
            type='Income',
            amount=500.00,
            date=date(2024, 10, 1),
            description='Bonus'
        )
        self.expense1 = IncomeExpense.objects.create(
            user_id=self.user,
            type='Expenses',
            amount=300.00,
            date=date(2024, 10, 1),
            description='Groceries'
        )

    def test_calculate_balance_view(self):
        """Test the calculate_balance function."""
        income_expenses = [self.income1, self.income2, self.expense1]
        balance_data = calculate_balance(income_expenses)

        self.assertEqual(balance_data[-1]['balance'], 1200.00)
        self.assertEqual(balance_data[0]['balance'], 1000.00)
        self.assertEqual(balance_data[-1]['check'], 1200.00)

    def test_get_income_expense_by_day_view(self):
        """Test the get_income_expense_by_day function for a specific date."""
        income_expenses = get_income_expense_by_day(self.user,
                                                    date(2024, 10, 1))
        self.assertEqual(len(income_expenses), 3)
        self.assertEqual(income_expenses[0].description, 'Salary')

    def test_calculate_balance_last_7_days_view(self):
        """Test calculate_balance_last_7_days for balance calculations over 7 days."""
        balance_7_days = calculate_balance_last_7_days(self.user,
                                                       date(2024, 10, 1))
        self.assertEqual(len(balance_7_days), 7)
        self.assertEqual(balance_7_days[0]['total_balance'], 1200.00)

    def test_sum_income_view(self):
        """Test the sum_income function for a specific day."""
        total_income = sum_income(self.user, date(2024, 10, 1))
        self.assertEqual(total_income, 1500.00)

    def test_sum_expense_view(self):
        """Test the sum_expense function for a specific day."""
        total_expense = sum_expense(self.user, date(2024, 10, 1))
        self.assertEqual(total_expense, 300.00)

    def test_sum_income_by_month_view(self):
        """Test the sum_income_by_month function for a specific month."""
        total_income_month = sum_income_by_month(self.user, 10)
        self.assertEqual(total_income_month, 1500.00)

    def test_sum_expense_by_month_view(self):
        """Test the sum_expense_by_month function for a specific month."""
        total_expense_month = sum_expense_by_month(self.user, 10)
        self.assertEqual(total_expense_month, 300.00)

    def test_calculate_income_expense_percentage_view(self):
        """Test calculate_income_expense_percentage for correct percentage calculations."""
        percentages = calculate_income_expense_percentage(1500.00, 300.00)
        self.assertAlmostEqual(percentages['income_percent'], 83.33, places=2)
        self.assertAlmostEqual(percentages['expense_percent'], 16.67, places=2)

    def test_delete_income_expense_view(self):
        """Test that an IncomeExpense object can be deleted successfully."""
        initial_count = IncomeExpense.objects.count()
        self.income1.delete()
        self.assertEqual(IncomeExpense.objects.count(), initial_count - 1)
        with self.assertRaises(IncomeExpense.DoesNotExist):
            IncomeExpense.objects.get(pk=self.income1.IncomeExpense_id)


class IncomeAndExpensesDetailViewTests(TestCase):
    """Tests for the detail view of income and expense entries."""

    def setUp(self):
        """Set up a user and an IncomeExpense entry for detail view testing."""
        # Create a user for testing
        self.user = User.objects.create_user(username='testuser',
                                             password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        # Create an IncomeExpense entry for testing
        self.income_expense = IncomeExpense.objects.create(
            user_id=self.user,
            type='Income',
            amount=100.00,
            date=timezone.now().date(),
            description='Test Income'
        )

    def test_income_and_expenses_detail_view_valid_date(self):
        """Test the detail view returns a successful response for a valid date."""
        response = self.client.get(reverse('moneymap:income-expense-detail',
                                           args=[self.income_expense.date]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'moneymap/income-expense-detail.html')

    def test_income_and_expenses_detail_view_no_data(self):
        """Test the detail view handles the case where no
        income/expense data exists for the given date."""
        future_date = timezone.now().date() + timezone.timedelta(days=1)
        response = self.client.get(
            reverse('moneymap:income-expense-detail', args=[future_date]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'moneymap/income-expense-detail.html')
        self.assertFalse(
            response.context['has_data'])  # Check that has_data is False


class HistoryViewTests(TestCase):
    """Tests for the history view of income and expense records."""

    def setUp(self):
        """Set up a user and create income/expense records for history testing."""
        # Create a user for testing
        self.user = User.objects.create_user(username='testuser',
                                             password='testpassword')
        self.client.login(username='testuser', password='testpassword')

    def create_income_expenses(self):
        """Create multiple income and expense entries for the user."""
        # Create IncomeExpense entries for the user
        IncomeExpense.objects.create(
            user_id=self.user,
            type='Income',
            amount=200.00,
            date=timezone.now().date(),
            description='Test Income 1'
        )
        IncomeExpense.objects.create(
            user_id=self.user,
            type='Income',
            amount=150.00,
            date=timezone.now().date() - timezone.timedelta(days=1),
            description='Test Income 2'
        )
        IncomeExpense.objects.create(
            user_id=self.user,
            type='Expenses',
            amount=100.00,
            date=timezone.now().date(),
            description='Test Expense 1'
        )
        IncomeExpense.objects.create(
            user_id=self.user,
            type='Expenses',
            amount=50.00,
            date=timezone.now().date() - timezone.timedelta(days=1),
            description='Test Expense 2'
        )

    def test_history_view_with_valid_date_range(self):
        """Test the history view returns the correct history for a valid date range."""
        self.create_income_expenses()

        start_date = (timezone.now().date() - timezone.timedelta(
            days=1)).strftime('%Y-%m-%d')
        end_date = timezone.now().date().strftime('%Y-%m-%d')

        response = self.client.get(reverse('moneymap:history'),
                                   {'startDate': start_date,
                                    'endDate': end_date})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moneymap/history.html')
        self.assertIn('history_list', response.context)

        # Check if the history_list contains the correct data
        history_list = response.context['history_list']
        self.assertEqual(len(history_list), 2)  # Two days of records
        self.assertEqual(history_list[0]['income'], 200.00)
        self.assertEqual(history_list[0]['expense'], 100.00)
        self.assertEqual(history_list[0]['total'], 100.00)

    def test_history_view_without_dates(self):
        """Test the history view returns all records when no dates are provided."""
        self.create_income_expenses()

        response = self.client.get(reverse('moneymap:history'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moneymap/history.html')
        self.assertIn('history_list', response.context)

        # Check that all records are included
        history_list = response.context['history_list']
        self.assertEqual(len(history_list), 2)  # Two days of records
        self.assertEqual(history_list[0]['income'], 200.00)
        self.assertEqual(history_list[0]['expense'], 100.00)

    def test_history_view_start_date_greater_than_end_date(self):
        """Test the history view handles the case where start date is greater than end date."""
        self.create_income_expenses()

        start_date = timezone.now().date().strftime('%Y-%m-%d')
        end_date = (timezone.now().date() - timezone.timedelta(
            days=1)).strftime('%Y-%m-%d')

        response = self.client.get(reverse('moneymap:history'),
                                   {'startDate': start_date,
                                    'endDate': end_date})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moneymap/history.html')
        self.assertIn('history_list', response.context)

        # Check that the history_list still returns the correct data
        history_list = response.context['history_list']
        self.assertEqual(len(history_list), 2)  # Two days of records
