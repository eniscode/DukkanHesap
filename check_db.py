from app import app, db, Income, Expense, DailyEntry

with app.app_context():
    print('\n📊 VERİTABANI DURUMU\n')
    
    print('=== GELİRLER (Income) ===')
    incomes = Income.query.order_by(Income.date.desc()).all()
    if incomes:
        for i in incomes:
            print(f'  ID:{i.id} | {i.date} | {i.category or "-"} | {i.amount:.2f} TL | {i.payment_type} | {i.description or "-"}')
    else:
        print('  (Boş)')
    print(f'Toplam: {len(incomes)} kayıt\n')
    
    print('=== GİDERLER (Expense) ===')
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    if expenses:
        for e in expenses:
            print(f'  ID:{e.id} | {e.date} | {e.category or "-"} | {e.amount:.2f} TL | {e.payment_type} | {e.description or "-"}')
    else:
        print('  (Boş)')
    print(f'Toplam: {len(expenses)} kayıt\n')
    
    print('=== GÜNLÜK GİRİŞLER (DailyEntry) ===')
    daily = DailyEntry.query.order_by(DailyEntry.date.desc()).all()
    if daily:
        for d in daily:
            print(f'  ID:{d.id} | {d.date} | Nakit:{d.cash_income:.2f} | Kart:{d.card_income:.2f} | Toplam:{d.total_income:.2f}')
    else:
        print('  (Boş)')
    print(f'Toplam: {len(daily)} kayıt\n')
