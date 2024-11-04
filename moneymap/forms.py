# temporary add goal and add money flow (transaction) forms
from django import forms
from .models import Goal

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'target_amount', 'description', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class AddMoneyForm(forms.Form):
    goal_id = forms.IntegerField(widget=forms.HiddenInput())
    goal_description = forms.CharField(max_length=255)
    goal_amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    distribute_evenly = forms.BooleanField(required=False)
    set_custom_percentages = forms.BooleanField(required=False)
    add_income_expense = forms.BooleanField(required=False)
