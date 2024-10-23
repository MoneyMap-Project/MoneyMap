def calculate_balance(income_expenses):
    balance = 0
    check = 0
    income_expense_with_balance = []

    for item in income_expenses:
        # Update balance based on the type of transaction
        if item.type == 'Income':
            balance += item.amount
            check += item.amount
        else:
            balance -= item.amount
            check -= item.amount

        # Add each record along with the updated balance to the list
        income_expense_with_balance.append({
            'description': item.description,
            'amount': item.amount,
            'balance': abs(balance),
            'type': item.type,
            'check': check,
        })

    return income_expense_with_balance
