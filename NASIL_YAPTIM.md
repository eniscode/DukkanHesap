# 📚 Dükkan Uygulaması - Sıfırdan Yapı Rehberi

## 1️⃣ BAŞLANGIÇ (Adım 1-2)

### Adım 1: Klasör Yapısı
```
Dukkan/
├── app.py              # Flask uygulaması + veritabanı modelleri
├── requirements.txt    # Python paketleri
├── dukkan.db          # SQLite veritabanı (otomatik oluşur)
├── static/
│   └── styles.css     # CSS tasarımı
└── templates/
    ├── base.html      # Ana sayfa şablonu
    ├── expenses.html
    ├── incomes.html
    ├── invoices.html
    ├── expense_edit.html
    ├── income_edit.html
    ├── invoice_edit.html
    ├── turnover.html
    └── report.html
```

### Adım 2: Virtual Environment Kurulumu
```bash
# Python virtual environment oluştur
python3 -m venv .venv

# Aktifleştir
source .venv/bin/activate  # macOS/Linux
# ya da
.venv\Scripts\activate  # Windows

# Gerekli paketleri yükle
pip install flask flask-sqlalchemy
```

---

## 2️⃣ VERİTABANI TASARIMI

### Veritabanı Mimarisi Nedir?
Veritabanı = Elektronik tablo sistemi

Böyle düşün:
```
Excel'de:
┌─────┬──────────┬────────┐
│ ID  │   Tarih  │ Tutar  │
├─────┼──────────┼────────┤
│ 1   │ 18.01.26 │1.234,56│
│ 2   │ 17.01.26 │ 567,89 │
└─────┴──────────┴────────┘

Veritabanında:
Table "income"
- id: 1, date: 2026-01-18, amount: 1234.56
- id: 2, date: 2026-01-17, amount: 567.89
```

### Flask-SQLAlchemy ile Model Tanımlama

**app.py içinde:**

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# VERİTABANI BAĞLANTISI
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dukkan.db"
db = SQLAlchemy(app)

# ===== TABLO 1: GELİRLER =====
class Income(db.Model):
    __tablename__ = "income"  # Tablo adı
    
    # Kolon tanımlamaları:
    id = db.Column(db.Integer, primary_key=True)  # Otomatik artan numara
    date = db.Column(db.Date, nullable=False)     # Tarih (boş olamaz)
    amount = db.Column(db.Float, nullable=False)  # Para miktarı
    category = db.Column(db.String(64))           # Kategori (boş olabilir)
    payment_type = db.Column(db.String(16))       # "cash" ya da "card"
    description = db.Column(db.Text)              # Uzun açıklama

# ===== TABLO 2: GİDERLER =====
class Expense(db.Model):
    __tablename__ = "expense"
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(64))
    payment_type = db.Column(db.String(16))  # "cash", "bank" ya da "card"
    description = db.Column(db.Text)

# ===== TABLO 3: FATURALAR =====
class Invoice(db.Model):
    __tablename__ = "invoice"
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
```

### Veri Tipleri Rehberi:
- `db.Integer` → Sayı (1, 2, 100)
- `db.String(64)` → Kısa metin (max 64 karakter)
- `db.Text` → Uzun metin (sınırsız)
- `db.Float` → Ondalık sayı (1.5, 234.56)
- `db.Date` → Tarih (2026-01-18)
- `db.Boolean` → Evet/Hayır (True/False)

---

## 3️⃣ FLASK ROUTES (URL Yolları)

Her URL'ye karşılık gelen Python fonksiyonu:

```python
# === GIDER SAYFASI ===
@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    if request.method == "POST":
        # Form verisi alıyoruz
        date_str = request.form.get("date")
        amount_str = request.form.get("amount")
        category = request.form.get("category")
        payment_type = request.form.get("payment_type")
        description = request.form.get("description")
        
        # Yeni gider kaydı oluştur
        new_expense = Expense(
            date=date_str,
            amount=float(amount_str),
            category=category,
            payment_type=payment_type,
            description=description
        )
        
        # Veritabanına kaydet
        db.session.add(new_expense)
        db.session.commit()
        
        flash("Gider başarıyla eklendi!", "success")
        return redirect("/expenses")
    
    # GET isteği: Tüm giderleri listele
    items = Expense.query.order_by(Expense.date.desc()).all()
    return render_template("expenses.html", items=items)

# === GIDER SİLME ===
@app.route("/expense/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    exp = Expense.query.get(expense_id)
    if exp:
        db.session.delete(exp)
        db.session.commit()
        flash("Gider silindi!", "success")
    return redirect("/expenses")

# === GIDER DÜZENLEME ===
@app.route("/expense/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    exp = Expense.query.get(expense_id)
    
    if request.method == "POST":
        # Form verilerini güncelle
        exp.date = request.form.get("date")
        exp.amount = float(request.form.get("amount"))
        exp.category = request.form.get("category")
        exp.payment_type = request.form.get("payment_type")
        exp.description = request.form.get("description")
        
        db.session.commit()
        flash("Gider güncellendi!", "success")
        return redirect("/expenses")
    
    return render_template("expense_edit.html", exp=exp)
```

### Veritabanı İşlemleri:

```python
# EKLEME
new_item = Income(date="2026-01-18", amount=1000, payment_type="cash")
db.session.add(new_item)
db.session.commit()

# OKUMA - Tümü al
all_items = Income.query.all()

# OKUMA - Şartle ara
january_items = Income.query.filter(Income.date.year == 2026).all()

# OKUMA - Sırala
latest = Income.query.order_by(Income.date.desc()).all()

# OKUMA - İlk kaydı al
first = Income.query.first()

# OKUMA - ID ile al
item = Income.query.get(1)

# GÜNCELLEME
item = Income.query.get(1)
item.amount = 2000
db.session.commit()

# SİLME
item = Income.query.get(1)
db.session.delete(item)
db.session.commit()
```

---

## 4️⃣ HTML TEMPLATES

### Temel Yapı (base.html):
```html
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Dükkan</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <header>
        <h1>Dükkan</h1>
        <nav>
            <a href="/expenses">Giderler</a>
            <a href="/incomes">Gelirler</a>
            <a href="/report">Rapor</a>
        </nav>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

### Form Sayfası (expenses.html):
```html
{% extends 'base.html' %}
{% block content %}

<h2>Gider Girişi</h2>

<!-- FORM -->
<form method="post">
    <label>
        Tarih:
        <input type="date" name="date" required>
    </label>
    
    <label>
        Tutar:
        <input type="number" name="amount" step="0.01" required>
    </label>
    
    <label>
        Kategori:
        <input type="text" name="category">
    </label>
    
    <label>
        Ödeme Tipi:
        <select name="payment_type">
            <option>nakit</option>
            <option>kart</option>
            <option>banka</option>
        </select>
    </label>
    
    <button type="submit">Ekle</button>
</form>

<!-- TABLO -->
<h3>Gider Listesi</h3>
<table>
    <thead>
        <tr>
            <th>Tarih</th>
            <th>Tutar</th>
            <th>Kategori</th>
            <th>İşlem</th>
        </tr>
    </thead>
    <tbody>
        {% for item in items %}
            <tr>
                <td>{{ item.date }}</td>
                <td>{{ item.amount }}</td>
                <td>{{ item.category }}</td>
                <td>
                    <a href="/expense/edit/{{ item.id }}">Düzenle</a>
                    <form action="/expense/delete/{{ item.id }}" method="post" style="display:inline;">
                        <button type="submit">Sil</button>
                    </form>
                </td>
            </tr>
        {% endfor %}
    </tbody>
</table>

{% endblock %}
```

### Jinja2 Template Sözdizimi:
```html
<!-- Değişkeni göster -->
{{ user_name }}

<!-- Koşul -->
{% if user_age >= 18 %}
    <p>Yetişkin</p>
{% else %}
    <p>Çocuk</p>
{% endif %}

<!-- Döngü -->
{% for item in items %}
    <p>{{ item.name }}: {{ item.price }}</p>
{% endfor %}

<!-- Filter -->
{{ amount | tr_currency }}  <!-- 1234.56 → 1.234,56 -->
{{ date | tr_short_date }}   <!-- 2026-01-18 → 18-Oca-26 -->

<!-- Kalıtım -->
{% extends 'base.html' %}
{% block content %}
    İçerik buraya
{% endblock %}
```

---

## 5️⃣ ÖZEL FONKSİYONLAR

### Türkçe Para Formatı:
```python
def parse_float(value, default=0.0):
    """
    1.234,56 → 1234.56 dönüştür
    """
    try:
        if isinstance(value, str):
            value = value.replace(".", "").replace(",", ".")
        return float(value)
    except:
        return default
```

### Template Filtreleri:
```python
@app.template_filter('tr_currency')
def tr_currency(value):
    """1234.56 → 1.234,56"""
    if value is None:
        return "0,00"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@app.template_filter('tr_day')
def tr_day(date_obj):
    """Tarihi günün adıyla göster"""
    days = ['PAZARTESİ', 'SALI', 'ÇARŞAMBA', 'PERŞEMBE', 'CUMA', 'CUMARTESİ', 'PAZAR']
    return days[date_obj.weekday()]
```

---

## 6️⃣ SUNUCUYU ÇALIŞTIRMA

```python
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Veritabanı tablolarını oluştur
    
    app.run(debug=True, host="127.0.0.1", port=5055)
```

Komut satırında:
```bash
python app.py
```

Tarayıcıda: `http://127.0.0.1:5055`

---

## 7️⃣ ÖZET: FLASK AKIŞI

```
1. Kullanıcı /expenses URL'sine tıklar
                    ↓
2. Flask "/expenses" route'unu bulur
                    ↓
3. Eğer POST (form gönderdi):
   - Form verilerini al
   - Yeni Expense nesnesi oluştur
   - db.session.add() ile ekle
   - db.session.commit() ile kaydet
   - Başarı mesajı göster
                    ↓
4. HTML template'ini (expenses.html) render et
                    ↓
5. Jinja2 template'ini işle:
   - {% for item in items %} döngüsü
   - {{ item.amount | tr_currency }} filtresini uygula
   - HTML'i tarayıcıya gönder
```

---

## 8️⃣ DEBUGGING TİPLERİ

### SQL Sorgularını Görmek:
```python
from sqlalchemy.orm import Query
print(Expense.query.filter(...).statement)
```

### Veritabanı İçeriğini Kontrol Etmek:
```python
# Python shell'de
from app import app, db, Expense
with app.app_context():
    all_expenses = Expense.query.all()
    for exp in all_expenses:
        print(f"{exp.date}: {exp.amount}")
```

### Flask Shell:
```bash
flask shell
>>> from app import Expense
>>> Expense.query.all()
```

---

## 9️⃣ ÜRETIM İÇİN (Production):

```bash
# Gunicorn kurulumu
pip install gunicorn

# Çalıştırma
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

## 🔟 KAYNAKLAR

- Flask Docs: https://flask.palletsprojects.com/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/
- Jinja2 Template: https://jinja.palletsprojects.com/
- SQLite: https://www.sqlite.org/

---

**İpuçları:**
- `db.session.commit()` yapmadığın sürece değişiklikler kaydedilmez
- Sorgu sonuçları lazy-loaded (gerekene kadar yüklenmez)
- `__repr__` metodu ekleyerek debugging'i kolaylaştırabilirsin
- Transaction'lar için `db.session.rollback()` kullan
