from unittest.mock import Mock
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from moneymap.models import Goal, IncomeExpense
from moneymap.service_addsavingmoney import (
    validate_goal_end_dates,
    validate_amount,
    check_goals_availability,
    distribute_savings,
    handle_goal_error
)

User = get_user_model()

class AddSavingMoneyServiceTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser',
                                             password='testpassword')

        # Create a test goal for use in tests
        self.goal = Goal.objects.create(
            user_id=self.user,
            title='Save for Vacation',
            description='Goal to save money for vacation',
            target_amount=Decimal('1000.00'),
            current_amount=Decimal('200.00'),
            start_date='2023-01-01',
            end_date='2023-12-31'
        )

        # Create an expired goal for testing
        self.goal_expired = Goal.objects.create(
            user_id=self.user,
            title='Expired Goal',
            description='A goal that is already expired',
            target_amount=Decimal('500.00'),
            current_amount=Decimal('100.00'),
            start_date='2022-01-01',
            end_date='2023-01-01'
        )

    def test_validate_goal_end_dates(self):
        # Simulate a mock request object
        request = Mock()

        # Test with goals that are valid
        goals = Goal.objects.filter(user_id=self.user)
        response = validate_goal_end_dates(goals, request)
        self.assertEqual(response.status_code,
                         302)

        # Test with expired goals
        expired_goals = Goal.objects.filter(user_id=self.user,
                                            end_date__lt='2023-12-01')
        response = validate_goal_end_dates(expired_goals, request)
        self.assertIsNotNone(
            response)

    def test_validate_amount(self):
        # Simulate a mock request object
        request = Mock()

        # Test with a valid amount
        amount = Decimal('100.00')
        response = validate_amount(amount, request)
        self.assertEqual(response, amount)

        # Test with an invalid (zero) amount
        response = validate_amount(Decimal('0.00'), request)
        self.assertEqual(response.status_code,
                         302)

        # Test with a negative amount
        response = validate_amount(Decimal('-50.00'), request)
        self.assertEqual(response.status_code,
                         302)

    def test_check_goals_availability(self):
        # Simulate a mock request object
        request = Mock()

        amount_decimal = Decimal('800.00')
        response = check_goals_availability(
            Goal.objects.filter(user_id=self.user), amount_decimal, request)
        self.assertIsNone(
            response)

        # Test with an amount that exceeds the total available space
        amount_decimal = Decimal('1500.00')
        response = check_goals_availability(
            Goal.objects.filter(user_id=self.user), amount_decimal, request)
        self.assertIsNotNone(
            response)

    def test_distribute_savings(self):
        # Simulate a mock request object
        request = Mock()

        amount_decimal = Decimal('500.00')
        parsed_date = '2023-12-01'
        add_to_income_expense = True

        params = {
            'goals': [self.goal],
            'amount_decimal': amount_decimal,
            'add_to_income_expense': add_to_income_expense,
            'parsed_date': parsed_date,
            'user': self.user,
            'request': request
        }
        # response = distribute_savings([self.goal], amount_decimal,add_to_income_expense, parsed_date,self.user, request)
        response = distribute_savings(params)
        self.assertIsNone(
            response)
        self.assertEqual(self.goal.current_amount, Decimal(
            '700.00'))

        # Verify that an IncomeExpense record is created
        income_expense = IncomeExpense.objects.first()
        self.assertIsNotNone(income_expense)
        self.assertEqual(income_expense.amount, Decimal('500.00'))

    def test_handle_goal_error(self):
        # Simulate a mock request object
        request = Mock()

        error_message = 'Test error'
        redirect_url = 'moneymap:add_money_goals'
        tag = 'goal'

        response = handle_goal_error(request, error_message, redirect_url, tag)
        self.assertIsNotNone(response)
