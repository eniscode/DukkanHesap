# 🔍 GERÇEK KOD ANALIZI - app.py

## VERİTABANI BAĞLANTISI
```
DATABASE URI = "sqlite:///dukkan.db"
                         └─ Proje klasöründe SQLite dosyası oluştur
```

## TEMEL AKIŞ (Gider örneği):

1. **Gider ekleme:**
```python
# HTML FORMU:
<form method="post" action="/expenses">
    <input name="date" value="2026-01-18">
    <input name="amount" value="1234,56">
    <input name="category" value="mal alış">
    <input name="payment_type" value="cash">
</form>

# Flask Fonksiyonu:
@app.route("/expenses", methods=["POST"])
def add_expense():
    # Form verilerini al
    date = request.form.get("date")           # "2026-01-18"
    amount = request.form.get("amount")       # "1234,56" (string)
    category = request.form.get("category")   # "mal alış"
    payment_type = request.form.get("payment_type")  # "cash"
    
    # String'i float'a dönüştür
    amount = parse_float(amount)  # 1234.56
    
    # Yeni kaydı oluştur
    new_expense = Expense(
        date=date,
        amount=amount,
        category=category,
        payment_type=payment_type
    )
    
    # Veritabanına ekle
    db.session.add(new_expense)
    db.session.commit()  # ← Bu olmadan veri kaydedilmez!
    
    # Kullanıcıya göster
    flash("Gider eklendi!", "success")
    return redirect("/expenses")

# SONUÇ: dukkan.db dosyasında yeni satır oluşturuldu
```

2. **Giderleri listele:**
```python
@app.route("/expenses", methods=["GET"])
def view_expenses():
    # Tüm giderleri date'e göre ters sırala (en yeni önce)
    items = Expense.query.order_by(Expense.date.desc()).all()
    
    # HTML template'ine gönder
    return render_template("expenses.html", items=items)

# expenses.html'de:
{% for item in items %}
    <tr>
        <td>{{ item.date }}</td>
        <td>{{ item.amount }}</td>
        <td>{{ item.category }}</td>
    </tr>
{% endfor %}
```

3. **Gider düzenle:**
```python
@app.route("/expense/edit/<int:expense_id>", methods=["POST"])
def edit_expense(expense_id):
    # ID ile kaydı bul
    exp = Expense.query.get(expense_id)  # ← ID=5 olan satırı getir
    
    # Alanları güncelle
    exp.amount = parse_float(request.form.get("amount"))
    exp.category = request.form.get("category")
    
    # Veritabanında güncelle
    db.session.commit()
```

4. **Gider sil:**
```python
@app.route("/expense/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    # ID ile kaydı bul
    exp = Expense.query.get(expense_id)
    
    # Sil
    db.session.delete(exp)
    db.session.commit()  # ← Veritabanından sil
```

## RAPOR HESAPLAMALARI

```python
@app.route("/report")
def report():
    # Tüm gelir kayıtlarını getir
    incomes = db.session.query(Income).all()  # ← SELECT * FROM income
    
    # Tüm gider kayıtlarını getir
    expenses = db.session.query(Expense).all()  # ← SELECT * FROM expense
    
    # Aylıklara göre grupla
    monthly_data = {}
    for income in incomes:
        key = (income.date.year, income.date.month)  # (2026, 1)
        if key not in monthly_data:
            monthly_data[key] = {"sales": 0, "expenses": 0}
        monthly_data[key]["sales"] += income.amount
    
    # Gelir - Gider = Kar
    # Kar / Gelir * 100 = Marj %
    
    return render_template("report.html", report_list=report_list)
```

## VERITABANININ İÇERİSİ

dukkan.db dosyası 4 tablodan oluşur:

### Tablo 1: income
```
┌────┬────────────┬────────┬──────────────┬──────────────┐
│ id │    date    │ amount │  category    │ payment_type │
├────┼────────────┼────────┼──────────────┼──────────────┤
│ 1  │ 2026-01-18 │ 1000.0 │ satış        │ cash         │
│ 2  │ 2026-01-17 │ 2500.5 │ ek gelir     │ card         │
└────┴────────────┴────────┴──────────────┴──────────────┘
```

### Tablo 2: expense
```
┌────┬────────────┬────────┬──────────────┬──────────────┐
│ id │    date    │ amount │  category    │ payment_type │
├────┼────────────┼────────┼──────────────┼──────────────┤
│ 1  │ 2026-01-18 │  500.0 │ mal alış     │ cash         │
│ 2  │ 2026-01-17 │ 1200.0 │ yeşillik     │ bank         │
└────┴────────────┴────────┴──────────────┴──────────────┘
```

### Tablo 3: invoice
```
┌────┬────────────┬────────┬──────────────────┐
│ id │    date    │ amount │  description     │
├────┼────────────┼────────┼──────────────────┤
│ 1  │ 2026-01-18 │5000.00 │ Aylık tedarik    │
│ 2  │ 2026-01-15 │3500.00 │ Araç bakım       │
└────┴────────────┴────────┴──────────────────┘
```

### Tablo 4: daily_entry
```
┌────┬────────────┬──────────────┬──────────────┬──────────────┐
│ id │    date    │ cash_income  │ card_income  │ total_income │
├────┼────────────┼──────────────┼──────────────┼──────────────┤
│ 1  │ 2026-01-18 │ 1000.0       │ 500.0        │ 1500.0       │
└────┴────────────┴──────────────┴──────────────┴──────────────┘
```

## SQL SORGUYA ÇEVRILME

Arka planda SQLAlchemy, Python kodunu SQL'e çevirir:

```python
# Python:
items = Expense.query.filter(Expense.amount > 500).all()

# SQL'ye dönüşür:
SELECT * FROM expense WHERE amount > 500;
```

## ORM vs SQL

```python
# ORM Yöntemi (SQLAlchemy) - Başlangıçta kolay
expense = Expense.query.get(1)
expense.amount = 2000
db.session.commit()

# SQL Yöntemi - Direkt SQL
db.session.execute("UPDATE expense SET amount = 2000 WHERE id = 1")

# ORM'in avantajları:
# - Python nesneleri ile çalış (daha okunaklı)
# - SQL injection riskini azalt
# - Veritabanı türünden bağımsız (SQLite, PostgreSQL vb.)
```

## SESSION NEDİR?

SQLAlchemy'de session = "çalışma alanı"

```python
# 1. Nesne oluştur (henüz veritabanında yok)
new_expense = Expense(amount=100)

# 2. Session'a ekle (bellekte hazırla)
db.session.add(new_expense)

# 3. Commit et (veritabanına kaydet)
db.session.commit()

# Eğer hata varsa:
db.session.rollback()  # Geri al
```

## DEBUGGING SORGULARI

```python
# Query'nin SQL'ini görmek
query = Expense.query.filter(Expense.amount > 500)
print(query.statement)

# Hızlı debug
print(query)  # <Query ...>
print(list(query))  # Verileri göster

# Kaç sonuç
count = Expense.query.count()

# İlki al
first = Expense.query.first()

# Son 10
last_10 = Expense.query.order_by(Expense.id.desc()).limit(10).all()
```

## ÖZET: VERITABANINA VERİ EKLEME YOLU

```
HTML Form
   ↓ (POST)
Flask Route (/expenses)
   ↓
Form verisi al (request.form)
   ↓
Python nesnesi oluştur (Expense(...))
   ↓
db.session.add()
   ↓
db.session.commit()
   ↓
SQLite dosyasına SQL INSERT komutu gönder
   ↓
dukkan.db dosyasında veri kaydedilir
```

İşte tamam! Sıfırdan yapacaksan bu adımları takip et:
1. app.py oluştur
2. Models tanımla (class definitions)
3. Routes yaz (@app.route)
4. Templates oluştur (HTML)
5. CSS stili ekle
6. Çalıştır (python app.py)
