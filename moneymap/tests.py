import datetime

from django.contrib.auth.models import User
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse

from .models import IncomeExpense
from .utils import calculate_balance


# Create your tests here.

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


class IncomeExpenseUtilsTests(TestCase):
    """Test the calculate_balance utility function."""

    def test_calculate_balance(self):
        """Test if the balance for today is calculated correctly, line by line."""

        user = User.objects.create_user(username='testuser',
                                        password='testpassword')
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

        income_expenses_today = IncomeExpense.objects.filter(user_id=user,
                                                             date=today).order_by(
            'date')
        income_expense_with_balance = calculate_balance(income_expenses_today)

        self.assertEqual(income_expense_with_balance[0]['balance'],
                         200.00)  # First balance
        self.assertEqual(income_expense_with_balance[1]['balance'],
                         150.00)  # After expense
        self.assertEqual(income_expense_with_balance[2]['balance'],
                         250.00)  # Final balance after second income
