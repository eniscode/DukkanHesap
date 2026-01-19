import os
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dukkan.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --------------------
# MODELS
# --------------------
class DailyEntry(db.Model):
    __tablename__ = "daily_entry"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    cash_income = db.Column(db.Float, default=0.0, nullable=False)
    card_income = db.Column(db.Float, default=0.0, nullable=False)
    total_income = db.Column(db.Float, default=0.0, nullable=False)
    note = db.Column(db.Text, nullable=True)

    def sync_total(self):
        self.total_income = (self.cash_income or 0.0) + (self.card_income or 0.0)

class Income(db.Model):
    __tablename__ = "income"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(64), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(16), nullable=False)  # 'cash' or 'card'
    description = db.Column(db.Text, nullable=True)

class Expense(db.Model):
    __tablename__ = "expense"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(64), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(16), nullable=False)  # 'cash' / 'bank' / 'card'
    description = db.Column(db.Text, nullable=True)

class Invoice(db.Model):
    __tablename__ = "invoice"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

# --------------------
# HELPERS
# --------------------

def parse_float(value, default=0.0):
    """Parse Turkish formatted number: 1.234,56 -> 1234.56"""
    try:
        if isinstance(value, str):
            # Remove thousand separators (.) and replace decimal comma with dot
            value = value.replace(".", "").replace(",", ".")
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_date(value):
    if isinstance(value, (date, datetime)):
        return value.date() if isinstance(value, datetime) else value
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return date.today()


# --------------------
# TEMPLATE FILTERS (TR)
# --------------------
TR_DAYS = [
    "PAZARTESİ",
    "SALI",
    "ÇARŞAMBA",
    "PERŞEMBE",
    "CUMA",
    "CUMARTESİ",
    "PAZAR",
]

TR_MONTHS_SHORT = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
TR_MONTHS = [
    "OCAK",
    "ŞUBAT",
    "MART",
    "NİSAN",
    "MAYIS",
    "HAZİRAN",
    "TEMMUZ",
    "AĞUSTOS",
    "EYLÜL",
    "EKİM",
    "KASIM",
    "ARALIK",
]

@app.template_filter("tr_day")
def tr_day(value):
    d = parse_date(value)
    return TR_DAYS[d.weekday()]

@app.template_filter("tr_short_date")
def tr_short_date(value):
    d = parse_date(value)
    return f"{d.day}-{TR_MONTHS_SHORT[d.month-1]}-{str(d.year)[-2:]}"

@app.template_filter("tr_currency")
def tr_currency(value):
    try:
        n = float(value or 0)
    except Exception:
        n = 0.0
    s = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


# --------------------
# ROUTES
# --------------------
@app.route("/")
def index():
    return redirect(url_for("expenses"))


@app.route("/daily-entry", methods=["GET", "POST"]) 
def daily_entry():
    today = date.today()
    if request.method == "POST":
        form_date = parse_date(request.form.get("date"))
        cash_income = parse_float(request.form.get("cash_income"))
        card_income = parse_float(request.form.get("card_income"))
        note = request.form.get("note") or None

        entry = DailyEntry.query.filter_by(date=form_date).first()
        if entry is None:
            entry = DailyEntry(date=form_date)
            db.session.add(entry)
        
        entry.cash_income = cash_income
        entry.card_income = card_income
        entry.note = note
        entry.sync_total()

        try:
            db.session.commit()
            flash("Günlük giriş kaydedildi.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Hata: {e}", "error")
        
        return redirect(url_for("daily_entry"))

    # GET
    entry = DailyEntry.query.filter_by(date=today).first()
    return render_template("daily_entry.html", today=today, entry=entry)


@app.route("/expenses", methods=["GET", "POST"]) 
def expenses():
    if request.method == "POST":
        form_date = parse_date(request.form.get("date"))
        category = request.form.get("category") or "Yeşillik"
        amount = parse_float(request.form.get("amount"))
        payment_type = "cash"
        description = request.form.get("description") or None

        exp = Expense(date=form_date, category=category, amount=amount,
                      payment_type=payment_type, description=description)
        db.session.add(exp)
        try:
            db.session.commit()
            flash("Gider eklendi.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Hata: {e}", "error")

        return redirect(url_for("expenses"))

    # GET - Ay filtresi
    selected_month = request.args.get("month", "")
    
    if selected_month:
        # Seçili ay varsa filtrele (format: 2026-01)
        try:
            year, month = selected_month.split("-")
            year, month = int(year), int(month)
            items = Expense.query.filter(
                db.extract('year', Expense.date) == year,
                db.extract('month', Expense.date) == month
            ).order_by(Expense.date.desc(), Expense.id.desc()).all()
        except:
            items = Expense.query.order_by(Expense.date.desc(), Expense.id.desc()).all()
    else:
        # Tüm kayıtlar
        items = Expense.query.order_by(Expense.date.desc(), Expense.id.desc()).all()
    
    # Toplam hesapla
    total = sum(item.amount for item in items)
    
    return render_template("expenses.html", items=items, today=date.today(), 
                         selected_month=selected_month, total=total)


@app.route("/expense/delete/<int:id>", methods=["POST"])
def expense_delete(id):
    exp = Expense.query.get_or_404(id)
    db.session.delete(exp)
    try:
        db.session.commit()
        flash("Gider silindi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Hata: {e}", "error")
    return redirect(url_for("expenses"))


@app.route("/expense/edit/<int:id>", methods=["GET", "POST"])
def expense_edit(id):
    exp = Expense.query.get_or_404(id)
    if request.method == "POST":
        exp.date = parse_date(request.form.get("date"))
        exp.category = (request.form.get("category") or "").strip() or None
        exp.amount = parse_float(request.form.get("amount"))
        exp.payment_type = "cash"
        exp.description = request.form.get("description") or None
        try:
            db.session.commit()
            flash("Gider güncellendi.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Hata: {e}", "error")
        return redirect(url_for("expenses"))
    return render_template("expense_edit.html", exp=exp)


@app.route("/incomes", methods=["GET", "POST"]) 
def incomes():
    if request.method == "POST":
        form_date = parse_date(request.form.get("date"))
        category = request.form.get("category") or "Ciro"
        amount = parse_float(request.form.get("amount"))
        payment_type = "cash"
        description = request.form.get("description") or None

        inc = Income(date=form_date, category=category, amount=amount,
                     payment_type=payment_type, description=description)
        db.session.add(inc)
        try:
            db.session.commit()
            flash("Gelir eklendi.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Hata: {e}", "error")

        return redirect(url_for("incomes"))

    # GET - Ay filtresi
    selected_month = request.args.get("month", "")
    
    if selected_month:
        # Seçili ay varsa filtrele (format: 2026-01)
        try:
            year, month = selected_month.split("-")
            year, month = int(year), int(month)
            items = Income.query.filter(
                db.extract('year', Income.date) == year,
                db.extract('month', Income.date) == month
            ).order_by(Income.date.desc(), Income.id.desc()).all()
        except:
            items = Income.query.order_by(Income.date.desc(), Income.id.desc()).all()
    else:
        # Tüm kayıtlar
        items = Income.query.order_by(Income.date.desc(), Income.id.desc()).all()
    
    # Toplam hesapla
    total = sum(item.amount for item in items)
    
    return render_template("incomes.html", items=items, today=date.today(),
                         selected_month=selected_month, total=total)


@app.route("/income/delete/<int:id>", methods=["POST"])
def income_delete(id):
    inc = Income.query.get_or_404(id)
    db.session.delete(inc)
    try:
        db.session.commit()
        flash("Gelir silindi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Hata: {e}", "error")
    return redirect(url_for("incomes"))


@app.route("/income/edit/<int:id>", methods=["GET", "POST"])
def income_edit(id):
    inc = Income.query.get_or_404(id)
    if request.method == "POST":
        inc.date = parse_date(request.form.get("date"))
        inc.category = (request.form.get("category") or "").strip() or None
        inc.amount = parse_float(request.form.get("amount"))
        inc.payment_type = "cash"
        inc.description = request.form.get("description") or None
        try:
            db.session.commit()
            flash("Gelir güncellendi.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Hata: {e}", "error")
        return redirect(url_for("incomes"))
    return render_template("income_edit.html", inc=inc)


def _sum_daily_income(d):
    d = parse_date(d)
    a = db.session.query(db.func.coalesce(db.func.sum(DailyEntry.total_income), 0.0)).filter(DailyEntry.date == d).scalar() or 0.0
    b = db.session.query(db.func.coalesce(db.func.sum(Income.amount), 0.0)).filter(Income.date == d).scalar() or 0.0
    return a + b

def _sum_daily_expense(d):
    d = parse_date(d)
    exp_total = db.session.query(db.func.coalesce(db.func.sum(Expense.amount), 0.0)).filter(Expense.date == d).scalar() or 0.0
    inv_total = db.session.query(db.func.coalesce(db.func.sum(Invoice.amount), 0.0)).filter(Invoice.date == d).scalar() or 0.0
    return exp_total + inv_total

def _sum_range(model, column, start_d, end_d):
    return db.session.query(db.func.coalesce(db.func.sum(column), 0.0)).\
        filter(column != None).\
        filter(model.date >= start_d, model.date <= end_d).scalar() or 0.0

@app.route("/turnover")
def turnover():
    today = date.today()

    # Günlük
    daily_income = _sum_daily_income(today)
    daily_expense = _sum_daily_expense(today)
    daily_net = daily_income - daily_expense
    daily_margin = (daily_net / daily_income * 100.0) if daily_income > 0 else 0.0

    # Aylık (ayın 1'inden bugüne)
    month_start = today.replace(day=1)
    month_income = (
        _sum_range(DailyEntry, DailyEntry.total_income, month_start, today) +
        _sum_range(Income, Income.amount, month_start, today)
    )
    month_expense = (
        _sum_range(Expense, Expense.amount, month_start, today) +
        _sum_range(Invoice, Invoice.amount, month_start, today)
    )
    month_net = month_income - month_expense
    month_margin = (month_net / month_income * 100.0) if month_income > 0 else 0.0

    # Yıllık (1 Ocak'tan bugüne)
    year_start = today.replace(month=1, day=1)
    year_income = (
        _sum_range(DailyEntry, DailyEntry.total_income, year_start, today) +
        _sum_range(Income, Income.amount, year_start, today)
    )
    year_expense = (
        _sum_range(Expense, Expense.amount, year_start, today) +
        _sum_range(Invoice, Invoice.amount, year_start, today)
    )
    year_net = year_income - year_expense
    year_margin = (year_net / year_income * 100.0) if year_income > 0 else 0.0

    # Nakit/Kart dağılımı (toplam)
    total_cash_income = db.session.query(db.func.coalesce(db.func.sum(DailyEntry.cash_income), 0.0)).scalar() or 0.0
    total_card_income = db.session.query(db.func.coalesce(db.func.sum(DailyEntry.card_income), 0.0)).scalar() or 0.0

    return render_template(
        "turnover.html",
        daily_income=daily_income,
        daily_expense=daily_expense,
        daily_net=daily_net,
        daily_margin=daily_margin,
        month_income=month_income,
        month_expense=month_expense,
        month_net=month_net,
        month_margin=month_margin,
        year_income=year_income,
        year_expense=year_expense,
        year_net=year_net,
        year_margin=year_margin,
        total_cash_income=total_cash_income,
        total_card_income=total_card_income,
    )


@app.route("/invoices", methods=["GET", "POST"])
def invoices():
    if request.method == "POST":
        form_date = parse_date(request.form.get("date"))
        amount = parse_float(request.form.get("amount"))
        description = request.form.get("description") or None

        inv = Invoice(date=form_date, amount=amount, description=description)
        db.session.add(inv)
        try:
            db.session.commit()
            flash("Fatura eklendi.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Hata: {e}", "error")
        return redirect(url_for("invoices"))

    # GET - faturaları ay/yıl bazında grupla
    from collections import defaultdict
    items = Invoice.query.order_by(Invoice.date.desc()).all()
    
    # Aylık toplamlar
    monthly_totals = defaultdict(float)
    for inv in items:
        key = (inv.date.year, inv.date.month)
        monthly_totals[key] += inv.amount
    
    return render_template("invoices.html", items=items, monthly_totals=monthly_totals, today=date.today())


@app.route("/invoice/delete/<int:id>", methods=["POST"])
def invoice_delete(id):
    inv = Invoice.query.get_or_404(id)
    db.session.delete(inv)
    try:
        db.session.commit()
        flash("Fatura silindi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Hata: {e}", "error")
    return redirect(url_for("invoices"))


@app.route("/invoice/edit/<int:id>", methods=["GET", "POST"])
def invoice_edit(id):
    inv = Invoice.query.get_or_404(id)
    if request.method == "POST":
        inv.date = parse_date(request.form.get("date"))
        inv.amount = parse_float(request.form.get("amount"))
        inv.description = request.form.get("description") or None
        try:
            db.session.commit()
            flash("Fatura güncellendi.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Hata: {e}", "error")
        return redirect(url_for("invoices"))
    return render_template("invoice_edit.html", inv=inv)

@app.route("/report")
def report():
    from collections import defaultdict
    from datetime import datetime
    
    # Get all income and expense records grouped by month
    incomes = db.session.query(Income).all()
    expenses = db.session.query(Expense).all()
    invoices = db.session.query(Invoice).all()
    
    # Group by (year, month)
    monthly_data = defaultdict(lambda: {"sales": 0.0, "expenses": 0.0})
    
    for income in incomes:
        key = (income.date.year, income.date.month)
        monthly_data[key]["sales"] += income.amount
    
    for expense in expenses:
        key = (expense.date.year, expense.date.month)
        monthly_data[key]["expenses"] += expense.amount
    
    for invoice in invoices:
        key = (invoice.date.year, invoice.date.month)
        monthly_data[key]["expenses"] += invoice.amount
    
    # Build report list with calculations
    report_list = []
    for (year, month) in sorted(monthly_data.keys(), reverse=True):
        sales = monthly_data[(year, month)]["sales"]
        expenses = monthly_data[(year, month)]["expenses"]
        net = sales - expenses
        margin = (net / sales * 100) if sales > 0 else 0.0
        
        month_name = TR_MONTHS[month-1]
        report_list.append({
            "label": f"{month_name} {year}",
            "sales": sales,
            "expenses": expenses,
            "net": net,
            "margin": margin
        })
    
    # Overall totals
    total_income = sum(d["sales"] for d in report_list)
    total_expense = sum(d["expenses"] for d in report_list)
    total_net = total_income - total_expense
    total_margin = (total_net / total_income * 100) if total_income > 0 else 0.0

    return render_template(
        "report.html",
        report_list=report_list,
        total_income=total_income,
        total_expense=total_expense,
        total_net=total_net,
        total_margin=total_margin,
    )


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5055"))
    # DB tablolarını uygulama başlamadan oluştur
    with app.app_context():
        db.create_all()
    print(f"\n🚀 Sunucu başlatılıyor: http://{host}:{port}\n")
    app.run(host=host, port=port, debug=True)
