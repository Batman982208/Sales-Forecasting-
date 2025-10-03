import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt
# --- Database Connectors ---
# Use pymysql for MySQL connection as it's a pure Python client
import pymysql.cursors
# Use pyhive for Hive connection
from pyhive import hive

# --- Flask App Initialization ---
app = Flask(__name__)
# IMPORTANT: Change this secret key for production
app.config['SECRET_KEY'] = os.urandom(24) 
bcrypt = Bcrypt(app)

# --- Database Configuration ---
# This section has been updated with your credentials and corrected syntax.
DB_CONFIG = {
    'host': 'localhost',
    'user': 'flaskuser',
    'password': 'Flask123!',
    'db': 'flask_auth_db',
    'cursorclass': pymysql.cursors.DictCursor
}

# --- !! IMPORTANT HIVE CONFIGURATION !! ---
# You MUST replace these placeholder values with your actual Hive server details.
# This is the most common point of failure.
HIVE_CONFIG = {
    'host': 'localhost',          # <-- REPLACE with your Hive server's IP address or hostname
    'port': 10000,                # The default port for HiveServer2
    'username': 'ayush-dubey',         # <-- REPLACE with the username for executing Hive queries
    'database': 'mysalesdb'         # <-- REPLACE with the database containing your sales table
    # Add other params like 'password' or 'auth' if your setup requires them
}


# --- Database Connection Helpers ---
def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.err.OperationalError as e:
        print("--- MySQL CONNECTION ERROR ---")
        print(f"Could not connect to MySQL. Please check your DB_CONFIG settings (host, user, password, db).")
        print(f"Details: {e}")
        return None
    except pymysql.MySQLError as e:
        print(f"An unexpected error occurred with MySQL: {e}")
        return None

def get_hive_connection():
    """Establishes a connection to Hive."""
    try:
        print(f"Attempting to connect to Hive at {HIVE_CONFIG['host']}:{HIVE_CONFIG['port']}...")
        conn = hive.connect(**HIVE_CONFIG)
        print("Successfully connected to Hive.")
        return conn.cursor()
    except Exception as e:
        print("--- HIVE CONNECTION ERROR ---")
        print("Failed to connect to Hive. Please check your HIVE_CONFIG settings and ensure HiveServer2 is running.")
        print(f"Details: {e}")
        return None

# --- Decorators for Route Protection ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('signin'))
        return f(*args, **kwargs)
    return decorated_function

# --- User Authentication Routes ---

@app.route('/')
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    # SQL to fetch user by email
                    sql = "SELECT * FROM users WHERE email = %s"
                    cursor.execute(sql, (email,))
                    user = cursor.fetchone()
                
                if user and bcrypt.check_password_hash(user['password_hash'], password):
                    session['user_id'] = user['id']
                    session['user_name'] = user['first_name']
                    flash(f"Welcome back, {user['first_name']}!", 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Login Unsuccessful. Please check email and password', 'danger')
            finally:
                conn.close()
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Get form data
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        email = request.form['email']
        password = request.form['password']
        
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    # SQL to insert a new user
                    sql = "INSERT INTO users (first_name, last_name, email, password_hash) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (first_name, last_name, email, hashed_password))
                conn.commit()
                flash('Your account has been created! You are now able to log in.', 'success')
                return redirect(url_for('signin'))
            except pymysql.err.IntegrityError:
                flash('An account with that email already exists.', 'warning')
            finally:
                conn.close()
        else:
            flash('Database connection failed. Could not create account.', 'danger')
            
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('signin'))

# --- Dashboard and Data API Routes ---

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html')

@app.route('/api/sales_data')
@login_required
def get_sales_data():
    """
    API endpoint to fetch sales data from Hive.
    Accepts 'start_date' and 'end_date' as query parameters.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    cursor = get_hive_connection()
    if not cursor:
        return jsonify({"error": "Failed to connect to data warehouse"}), 500

    # IMPORTANT: Replace 'sales_records' with your actual Hive table name
    query = "SELECT orderid, product, category, region, quantity, priceperunit, totalsales, `date` FROM sales_records"
    
    conditions = []
    params = []
    if start_date:
        conditions.append("`date` >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("`date` <= %s")
        params.append(end_date)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    print("\n--- EXECUTING HIVE QUERY ---")
    print(f"Query: {query}")
    print(f"Parameters: {params}")
    
    try:
        cursor.execute(query, params)
        print("Hive query executed successfully.")
        
        columns = [desc[0].split('.')[-1] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        key_mapping = {
            'orderid': 'OrderID', 'product': 'Product', 'category': 'Category',
            'region': 'Region', 'quantity': 'Quantity', 'priceperunit': 'PricePerUnit',
            'totalsales': 'TotalSales', 'date': 'Date'
        }
        
        remapped_data = [
            {key_mapping.get(k.lower(), k): v for k, v in row.items()} for row in data
        ]
            
        return jsonify(remapped_data)
        
    except Exception as e:
        print("--- HIVE QUERY FAILED ---")
        print(f"An error occurred while executing the Hive query.")
        print(f"Details: {e}")
        return jsonify({"error": "An error occurred while fetching data from the data warehouse"}), 500

if __name__ == '__main__':
    app.run(debug=True)

