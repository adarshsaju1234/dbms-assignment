from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from db_config import get_db_connection

app = Flask(__name__)
app.secret_key = "supersecretkey"
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return User(user["id"], user["username"], user["email"]) if user else None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                           (username, email, hashed_pw))
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except:
            flash("Username or email already taken!", "danger")
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user['password_hash'], password):
            login_user(User(user["id"], user["username"], user["email"]))
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!", "danger")

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Handle expense entry
    if request.method == 'POST':
        category_id = request.form['category']
        amount = request.form['amount']
        date = request.form['date']

        cursor.execute("INSERT INTO expenses (user_id, category_id, amount, date) VALUES (%s, %s, %s, %s)",
                       (current_user.id, category_id, amount, date))
        conn.commit()
        flash("Expense added successfully!", "success")

    # Fetch categories for dropdown
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    # Fetch expenses
    cursor.execute("""
        SELECT e.id, c.name AS category, e.amount, e.date 
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s
    """, (current_user.id,))
    expenses = cursor.fetchall()

    cursor.execute("SELECT SUM(amount) AS total FROM expenses WHERE user_id = %s", (current_user.id,))
    total_expense = cursor.fetchone()['total'] or 0

    cursor.execute("""
        SELECT c.name, SUM(e.amount) AS total 
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s
        GROUP BY c.name
    """, (current_user.id,))
    category_expenses = cursor.fetchall()
    
    conn.close()

    return render_template('dashboard.html', expenses=expenses, total=total_expense, category_expenses=category_expenses, categories=categories)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
