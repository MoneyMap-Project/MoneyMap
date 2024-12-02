"""
Unit tests for the Goal model and related services/views in the moneymap application.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from moneymap.models import Goal
from moneymap.service_addgoals import get_goals_data

User = get_user_model()


class GoalModelTests(TestCase):
    """Test the Goal model."""

    def setUp(self):
        """Set up a user and sample goal for tests."""
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.sample_goal = Goal.objects.create(
            user_id=self.user,
            title='Test Goal',
            description='Test description',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            target_amount=1000.00,
            current_amount=0.00
        )

    def test_create_goal(self):
        """Test creating a goal object."""
        self.assertEqual(self.sample_goal.user_id, self.user)
        self.assertEqual(self.sample_goal.title, 'Test Goal')
        self.assertEqual(self.sample_goal.description, 'Test description')
        self.assertEqual(self.sample_goal.target_amount, 1000.00)
        self.assertEqual(self.sample_goal.current_amount, 0.00)
        self.assertTrue(isinstance(self.sample_goal.start_date, date))
        self.assertTrue(isinstance(self.sample_goal.end_date, date))

class GoalServiceTests(TestCase):
    """Test the goal-related service functions."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser',
                                             password='testpassword')
        self.today = date.today()

        # Create goals with different statuses
        self.active_goal = Goal.objects.create(
            user_id=self.user,
            title='Active Goal',
            description='Test description',
            start_date=self.today - timedelta(days=5),
            end_date=self.today + timedelta(days=25),
            target_amount=1000.00,
            current_amount=250.00
        )

        self.completed_goal = Goal.objects.create(
            user_id=self.user,
            title='Completed Goal',
            description='Test description',
            start_date=self.today - timedelta(days=30),
            end_date=self.today - timedelta(days=1),
            target_amount=500.00,
            current_amount=500.00
        )

        self.future_goal = Goal.objects.create(
            user_id=self.user,
            title='Future Goal',
            description='Test description',
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=35),
            target_amount=2000.00,
            current_amount=0.00
        )

    def test_get_goals_data(self):
        """Test the get_goals_data service function."""
        goals = Goal.objects.filter(user_id=self.user)
        goals_data = get_goals_data(goals)

        # Test that all goals are included
        self.assertEqual(len(goals_data), 3)

        # Test active goal calculations
        active_goal_data = next(
            g for g in goals_data if g['title'] == 'Active Goal')
        self.assertEqual(active_goal_data['progress_percentage'],
                         25)  # 250/1000 * 100
        self.assertEqual(active_goal_data['days_remaining'], 25)
        self.assertEqual(active_goal_data['minimum_saving'], 30)  
        self.assertTrue(active_goal_data['trend'], 'Negative')

        # Test completed goal calculations
        completed_goal_data = next(
            g for g in goals_data if g['title'] == 'Completed Goal')
        self.assertEqual(completed_goal_data['progress_percentage'], 100)

        self.assertEqual(completed_goal_data['minimum_saving'], 0)  
        self.assertEqual(completed_goal_data['trend'], 'Negative') 

        # Test future goal calculations
        future_goal_data = next(
            g for g in goals_data if g['title'] == 'Future Goal')
        self.assertEqual(future_goal_data['progress_percentage'], 0)
        self.assertAlmostEqual(round(future_goal_data['minimum_saving'], 2), round(Decimal(57.14), 2))  
        self.assertEqual(future_goal_data['trend'], 'Negative')  

class GoalViewTests(TestCase):
    """Test the goal-related views."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser',
                                             password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        self.goal = Goal.objects.create(
            user_id=self.user,
            title='Test Goal',
            description='Test description',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            target_amount=1000.00,
            current_amount=250.00
        )

    def test_goals_view(self):
        """Test the main goals view."""
        response = self.client.get(reverse('moneymap:goals'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moneymap/goals.html')

        # Check that the context contains the goals data
        self.assertIn('goals_data', response.context)
        goals_data = response.context['goals_data']
        self.assertEqual(len(goals_data), 1)
        self.assertEqual(goals_data[0]['title'], 'Test Goal')

    def test_add_goals_view_get(self):
        """Test the add goals view GET request."""
        response = self.client.get(reverse('moneymap:add_goals'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moneymap/add_goals.html')

    def test_add_goals_view_post_valid(self):
        """Test adding a new goal with valid data."""
        goal_data = {
            'goal_title': 'New Goal',
            'goal_description': 'New description',
            'start_date': date.today().strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=30)).strftime(
                '%Y-%m-%d'),
            'target_amount': '1500.00'
        }

        response = self.client.post(reverse('moneymap:add_goals'), goal_data)
        self.assertRedirects(response, reverse('moneymap:goals'))

        # Verify the goal was created
        self.assertTrue(Goal.objects.filter(title='New Goal').exists())

    def test_add_goals_view_post_invalid(self):
        """Test adding a new goal with invalid data."""
        goal_data = {
            'goal_title': 'Invalid Goal',
            'goal_description': 'Invalid description',
            'start_date': date.today().strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=30)).strftime(
                '%Y-%m-%d'),
            'target_amount': 'not_a_number'
        }

        response = self.client.post(reverse('moneymap:add_goals'), goal_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moneymap/add_goals.html')
        self.assertIn('error', response.context)

        # Verify the goal was not created
        self.assertFalse(Goal.objects.filter(title='Invalid Goal').exists())
