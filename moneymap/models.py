"""Contains the models for the MoneyMap app.
Collect the data from the user and store it in the database."""

from django.db import models
from django.conf import settings
from decimal import Decimal


class Goal(models.Model):
    """Model for a goal."""
    # goal id as a primary key from database
    goal_id = models.AutoField(primary_key=True)
    # user_id as a foreign key
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, default="No description.")
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    start_date = models.DateField()
    end_date = models.DateField()

    def update_current_amount(self, amount_saved):
        """Update current amount with a new saving input."""
        self.current_amount += Decimal(amount_saved)
        self.save()

    def remaining_amount(self):
        """Calculate remaining amount to reach target."""
        return max(Decimal('0.00'), self.target_amount - self.current_amount)

    def __str__(self):
        return f"{self.description}"

class IncomeExpense(models.Model):
    """Model for the income expense."""
    IncomeExpense_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='income_expenses', null=False)

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

