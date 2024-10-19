from urllib import request

from django.shortcuts import render

def home(request):
    return render(request, 'moneymap/home.html')

def income_and_expenses(request):
    return render(request, 'moneymap/income-expenses.html')

def goals(request):
    return render(request, 'moneymap/goals.html')

def history(request):
    return render(request, 'moneymap/history.html')

def money_flow(request):
    return render(request, 'moneymap/money-flow.html')