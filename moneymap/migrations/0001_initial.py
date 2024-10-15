# Generated by Django 5.1.1 on 2024-10-15 16:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GoalAllocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('goal_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('target_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='IncomeExpense',
            fields=[
                ('IncomeExpense_id', models.AutoField(primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('income', 'Income'), ('expense', 'Expense'), ('saving', 'Saving')], max_length=7)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date', models.DateField()),
                ('description', models.CharField(max_length=255)),
                ('saved_to_income_expense', models.BooleanField(default=False)),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SavingEntry',
            fields=[
                ('saving_id', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('goal_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='moneymap.goal')),
            ],
        ),
    ]
