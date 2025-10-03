# Big Data Sales Analytics Dashboard
A full-stack web application I developed to demonstrate the integration of a Python web framework with a big data ecosystem. This project features a secure user authentication system and a dynamic dashboard that queries and visualizes sales data directly from an Apache Hive data warehouse.

Core Features
Secure User Authentication: I implemented a complete user registration and login system using Flask and MySQL, with password hashing handled by Flask-Bcrypt.

Dynamic Data Dashboard: The main dashboard fetches sales data directly from a Hive backend, ensuring the information is always up-to-date.

Live Data Filtering: I built an intuitive front-end interface that allows users to filter the sales data by a date range. The filtering logic is processed by a dedicated API endpoint that constructs and executes HiveQL queries in real-time.

RESTful API Backend: I designed a simple REST API using Flask to serve data to the front end, decoupling the client-side logic from the backend data processing.

Responsive Frontend: The user interface was built with modern HTML and Tailwind CSS to be fully responsive and provide a seamless experience on both desktop and mobile devices.

Technology Stack & Architecture
I architected this application to mirror a modern enterprise environment, where a user-facing web application needs to interact with a large-scale data warehouse for analytics.

Frontend:

HTML5

Tailwind CSS

JavaScript (for API calls and DOM manipulation)

Backend:

Framework: Flask

Authentication: Flask-Bcrypt for password hashing, Flask-Session for session management.

User Database:

Database: MySQL

Connector: PyMySQL

Data Warehouse & Big Data Ecosystem:

Storage: Hadoop Distributed File System (HDFS)

Data Warehouse: Apache Hive

Connector: PyHive for executing queries from the Flask application.

Setup and Installation
To get this project up and running locally, you will need Python 3.10+, Git, MySQL, and a working Hadoop/Hive environment.

1. Clone the Repository
git clone [https://github.com/Batman982208/Sales-Forecasting-.git]
cd your-repo-name

2. Set Up a Python Virtual Environment
# Create a virtual environment
python3 -m venv myenv

# Activate it 
source myenv/bin/activate

3. Install Dependencies
All required Python packages are listed in requirements.txt.

pip install -r requirements.txt

4. MySQL Database Setup
You need to create a database and a dedicated user for the application.

-- Connect to MySQL as the root user
mysql -u root -p

-- Create the database
CREATE DATABASE flask_auth_db;

-- Create a user and grant privileges (replace 'Flask123!' with a strong password)
CREATE USER 'flaskuser'@'localhost' IDENTIFIED BY 'Flask123!';
GRANT ALL PRIVILEGES ON flask_auth_db.* TO 'flaskuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;

Next, create the users table within the flask_auth_db database:

USE flask_auth_db;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

5. Hive Data Setup
Ensure your Hive server is running. Create a table (e.g., sales_records) and load your sales data CSV into it.

Example HiveQL:

CREATE TABLE IF NOT EXISTS sales_records (
    OrderID STRING,
    Product STRING,
    Category STRING,
    Region STRING,
    Quantity INT,
    PricePerUnit DOUBLE,
    TotalSales DOUBLE,
    `Date` DATE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ',';

-- Load data from a file stored in HDFS
LOAD DATA INPATH '/path/to/your/sales_data.csv' OVERWRITE INTO TABLE sales_records;

6. Configure the Application
Open the app.py file and update the database configuration dictionaries with your own credentials.

Update DB_CONFIG for MySQL:

DB_CONFIG = {
    'host': 'localhost',
    'user': 'flaskuser',
    'password': 'Flask123!', # The password you set in Step 4
    'db': 'flask_auth_db',
    'cursorclass': pymysql.cursors.DictCursor
}

Update HIVE_CONFIG for Hive:

HIVE_CONFIG = {
    'host': 'your_hive_server_ip', # e.g., '127.0.0.1' or your VM's IP
    'port': 10000,
    'username': 'hadoop',       # Your Hive username
    'database': 'default'         # The database containing 'sales_records'
}

7. Run the Application
With your virtual environment activated, you can now start the Flask server.

python app.py

Open your browser and navigate to http://127.0.0.1:5000.
