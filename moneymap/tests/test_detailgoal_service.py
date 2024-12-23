"""Unit tests for related services using in GoalsDetailView."""

from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from moneymap.models import Goal
from moneymap.service_detailgoals import (
    calculate_days_remaining,
    calculate_trend,
    calculate_saving_progress,
    calculate_days_elapsed,
    calculate_avg_saving,
    calculate_saving_shortfall,
    get_all_saving_specific_goal,
    get_all_goals,
    get_current_total_days
)

User = get_user_model()

START_DATE = timezone.localtime(timezone.now())
END_DATE = timezone.localtime(timezone.now()).date() + timedelta(days=30)

class GoalServiceTests(TestCase):
    def setUp(self):
        """Set up a user and sample goal for tests."""
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.sample_goal = Goal.objects.create(
            user_id=self.user,
            title='Test Goal',
            description='Test description',
            start_date=START_DATE,
            end_date=END_DATE,
            target_amount=1000.00,
            current_amount=0.00
        )

    def test_calculate_days_remaining(self):
        """Test calculate_days_remaining function."""
        self.assertLessEqual(calculate_days_remaining(self.sample_goal.end_date), 31)

    def test_calculate_trend(self):
        """Test calculate_trend function."""
        result = calculate_trend(self.sample_goal.goal_id)
        self.assertEqual(result[0]['trend'],
                         'Negative')

    def test_calculate_saving_progress(self):
        """Test calculate_saving_progress function."""
        self.assertEqual(calculate_saving_progress(self.sample_goal), 0.00)

    def test_calculate_days_elapsed(self):
        """Test calculate_days_elapsed function."""
        result = calculate_days_elapsed(START_DATE, self.sample_goal)
        self.assertEqual(result, 0)

    def test_calculate_avg_saving(self):
        """Test calculate_avg_saving function."""
        result = calculate_avg_saving(self.user, date.today(), self.sample_goal.goal_id)
        self.assertEqual(result, 0.00)

    def test_calculate_saving_shortfall(self):
        """Test calculate_saving_shortfall function."""
        result = calculate_saving_shortfall(self.sample_goal.goal_id)
        self.assertLessEqual(result, Decimal('33.33'))

    def test_all_saving_specific_goal(self):
        """Test get_all_saving_specific_goal function."""
        self.assertEqual(get_all_saving_specific_goal(self.sample_goal).count(), 0)

    def test_all_goals(self):
        """Test get_all_goals function."""
        self.assertEqual(get_all_goals(self.user).count(), 1)
