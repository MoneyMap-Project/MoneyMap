"""Contains the models for the MoneyMap app.
Collect the data from the user and store it in the database."""

from decimal import Decimal
from django.db import models
from django.conf import settings


class Goal(models.Model):
    """Model for a goal."""
    # goal id as a primary key from database
    goal_id = models.AutoField(primary_key=True)
    # user_id as a foreign key
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=255, default='No title')
    description = models.CharField(max_length=255, default='No description')

    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
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


class Tag(models.Model):
    """Model to store tag names independently."""
    name = models.CharField(max_length=100, unique=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='tag')

    def __str__(self):
        return self.name


class IncomeExpense(models.Model):
    IncomeExpense_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='income_expenses')
    tags = models.ManyToManyField(Tag, blank=True)

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
        return f"{self.description}"


class SavingEntry(models.Model):
    """ Model for saving entries."""
    saving_id = models.AutoField(primary_key=True)
    goal_id = models.ForeignKey('Goal', on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.amount} saved on {self.date} at {self.goal_id}"
