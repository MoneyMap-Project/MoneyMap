"""Contains the models for the MoneyMap app.
Collect the data from the user and store it in the database."""

from django.db import models
from django.conf import settings


class Goal(models.Model):
    """Model for a goal."""
    # goal id as a primary key from database
    goal_id = models.AutoField(primary_key=True)
    # user_id as a foreign key
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    @property
    def total_days(self):
        """Calculate the total days between
        the start and end date for use in the trend graph."""
        return (self.end_date - self.start_date).days

    def days_remaining(self):
        """Calculate the days remaining to reach the goal."""
        return (self.end_date - self.start_date).days

    def total_saved(self):
        """Calculate the total saved amount for the goal."""
        pass

    def min_saving_per_day(self):
        """Calculate the minimum saving per day to reach the goal."""
        pass

    def avg_saving_per_day(self):
        """Calculate the average saving from start date until current date."""
        pass

    def current_progress(self):
        """Calculate the current progress of the goal."""
        pass

    def progress_trend(self):
        """Calculate the trend of the goal."""
        pass

    def progress_graph(self):
        """Calculate the progress graph of the goal."""
        pass


class GoalAllocation(models.Model):
    """Model for the allocation of a goal."""
    # user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    # goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    # percentage =
    pass


class IncomeExpense(models.Model):
    """Model for the income expense."""
    IncomeExpense_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='income_expenses')

    expense_type = (
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('saving', 'Saving'),
    )
    type = models.CharField(
        max_length=15,
        choices=expense_type
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255)
    saved_to_income_expense = models.BooleanField(default=False)

    # currency_id = pass will be added later

    def __str__(self):
        return self.description
        # return f"{self.type} of {self.amount} on {self.date}"


class SavingEntry(models.Model):
    """ Model for saving entries."""
    saving_id = models.AutoField(primary_key=True)
    goal_id = models.ForeignKey('Goal', on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.amount} saved on {self.date} at {self.goal_id}"
