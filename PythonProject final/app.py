from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'


# Database initialization
def init_db():
    conn = sqlite3.connect('bike_service.db')
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     name
                     TEXT
                     NOT
                     NULL,
                     email
                     TEXT
                     UNIQUE
                     NOT
                     NULL,
                     phone
                     TEXT
                     NOT
                     NULL,
                     password
                     TEXT
                     NOT
                     NULL,
                     address
                     TEXT,
                     created_at
                     TIMESTAMP
                     DEFAULT
                     CURRENT_TIMESTAMP
                 )''')

    # Bikes table
    c.execute('''CREATE TABLE IF NOT EXISTS bikes
    (
        id
        INTEGER
        PRIMARY
        KEY
        AUTOINCREMENT,
        user_id
        INTEGER
        NOT
        NULL,
        brand
        TEXT
        NOT
        NULL,
        model
        TEXT
        NOT
        NULL,
        year
        INTEGER,
        registration_number
        TEXT,
        FOREIGN
        KEY
                 (
        user_id
                 ) REFERENCES users
                 (
                     id
                 )
        )''')

    # Services table
    c.execute('''CREATE TABLE IF NOT EXISTS services
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     name
                     TEXT
                     NOT
                     NULL,
                     description
                     TEXT,
                     price
                     REAL
                     NOT
                     NULL,
                     duration
                     TEXT,
                     category
                     TEXT
                 )''')

    # Bookings table
    c.execute('''CREATE TABLE IF NOT EXISTS bookings
    (
        id
        INTEGER
        PRIMARY
        KEY
        AUTOINCREMENT,
        user_id
        INTEGER
        NOT
        NULL,
        bike_id
        INTEGER
        NOT
        NULL,
        service_id
        INTEGER
        NOT
        NULL,
        booking_date
        DATE
        NOT
        NULL,
        booking_time
        TEXT
        NOT
        NULL,
        status
        TEXT
        DEFAULT
        'Pending',
        notes
        TEXT,
        created_at
        TIMESTAMP
        DEFAULT
        CURRENT_TIMESTAMP,
        FOREIGN
        KEY
                 (
        user_id
                 ) REFERENCES users
                 (
                     id
                 ),
        FOREIGN KEY
                 (
                     bike_id
                 ) REFERENCES bikes
                 (
                     id
                 ),
        FOREIGN KEY
                 (
                     service_id
                 ) REFERENCES services
                 (
                     id
                 )
        )''')

    # Insert default services if empty
    c.execute('SELECT COUNT(*) FROM services')
    if c.fetchone()[0] == 0:
        services = [
            ('General Service', 'Complete bike checkup including oil change, filter cleaning, and basic adjustments',
             499.00, '2-3 hours', 'Maintenance'),
            ('Oil Change', 'Engine oil replacement with quality oil', 299.00, '30 mins', 'Maintenance'),
            ('Brake Service', 'Brake pad replacement and brake system inspection', 399.00, '1 hour', 'Safety'),
            ('Chain Service', 'Chain cleaning, lubrication, and tension adjustment', 199.00, '45 mins', 'Maintenance'),
            ('Tire Replacement', 'Front or rear tire replacement with quality tires', 799.00, '1 hour', 'Tires'),
            ('Battery Replacement', 'Battery testing and replacement if needed', 599.00, '30 mins', 'Electrical'),
            ('Engine Tuning', 'Carburetor cleaning, spark plug replacement, and engine optimization', 699.00,
             '3-4 hours', 'Performance'),
            ('Full Body Wash', 'Complete exterior cleaning and polishing', 249.00, '1 hour', 'Cleaning'),
            ('Clutch Repair', 'Clutch plate inspection and replacement', 899.00, '2-3 hours', 'Repair'),
            ('Electrical Repair', 'Wiring, lights, and electrical system repair', 449.00, '1-2 hours', 'Electrical'),
            ('Suspension Service', 'Fork oil change and suspension adjustment', 549.00, '2 hours', 'Performance'),
            ('Wheel Alignment', 'Front and rear wheel alignment and balancing', 299.00, '1 hour', 'Safety')
        ]
        c.executemany('INSERT INTO services (name, description, price, duration, category) VALUES (?, ?, ?, ?, ?)',
                      services)

    conn.commit()
    conn.close()


# Initialize database on startup
init_db()


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# Database helper
def get_db():
    conn = sqlite3.connect('bike_service.db')
    conn.row_factory = sqlite3.Row
    return conn


# Routes
@app.route('/')
def index():
    conn = get_db()
    services = conn.execute('SELECT * FROM services LIMIT 6').fetchall()
    conn.close()
    return render_template('index.html', services=services)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))

        conn = get_db()
        try:
            conn.execute('INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)',
                         (name, email, phone, generate_password_hash(password)))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists!', 'error')
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash('Welcome back, ' + user['name'] + '!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    bikes = conn.execute('SELECT * FROM bikes WHERE user_id = ?', (session['user_id'],)).fetchall()

    bookings = conn.execute('''
                            SELECT b.*, s.name as service_name, s.price, bk.brand, bk.model
                            FROM bookings b
                                     JOIN services s ON b.service_id = s.id
                                     JOIN bikes bk ON b.bike_id = bk.id
                            WHERE b.user_id = ?
                            ORDER BY b.booking_date DESC LIMIT 5
                            ''', (session['user_id'],)).fetchall()

    conn.close()
    return render_template('dashboard.html', user=user, bikes=bikes, bookings=bookings)


@app.route('/services')
def services():
    conn = get_db()
    services = conn.execute('SELECT * FROM services ORDER BY category').fetchall()
    conn.close()

    # Group services by category
    categorized = {}
    for service in services:
        cat = service['category']
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(service)

    return render_template('services.html', categorized_services=categorized)


@app.route('/book-service', methods=['GET', 'POST'])
@login_required
def book_service():
    conn = get_db()

    if request.method == 'POST':
        bike_id = request.form['bike_id']
        service_id = request.form['service_id']
        booking_date = request.form['booking_date']
        booking_time = request.form['booking_time']
        notes = request.form.get('notes', '')

        conn.execute('''INSERT INTO bookings (user_id, bike_id, service_id, booking_date, booking_time, notes)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (session['user_id'], bike_id, service_id, booking_date, booking_time, notes))
        conn.commit()
        conn.close()

        flash('Service booked successfully!', 'success')
        return redirect(url_for('dashboard'))

    bikes = conn.execute('SELECT * FROM bikes WHERE user_id = ?', (session['user_id'],)).fetchall()
    services = conn.execute('SELECT * FROM services ORDER BY category').fetchall()
    selected_service = request.args.get('service_id')
    conn.close()

    return render_template('book_service.html', bikes=bikes, services=services, selected_service=selected_service)


@app.route('/add-bike', methods=['POST'])
@login_required
def add_bike():
    brand = request.form['brand']
    model = request.form['model']
    year = request.form.get('year')
    registration = request.form.get('registration_number')

    conn = get_db()
    conn.execute('INSERT INTO bikes (user_id, brand, model, year, registration_number) VALUES (?, ?, ?, ?, ?)',
                 (session['user_id'], brand, model, year, registration))
    conn.commit()
    conn.close()

    flash('Bike added successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/delete-bike/<int:bike_id>', methods=['POST'])
@login_required
def delete_bike(bike_id):
    conn = get_db()
    conn.execute('DELETE FROM bikes WHERE id = ? AND user_id = ?', (bike_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Bike removed successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form.get('address', '')

        conn.execute('UPDATE users SET name = ?, phone = ?, address = ? WHERE id = ?',
                     (name, phone, address, session['user_id']))
        conn.commit()
        session['user_name'] = name
        flash('Profile updated successfully!', 'success')

    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()

    return render_template('profile.html', user=user)


@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    conn = get_db()
    conn.execute('UPDATE bookings SET status = ? WHERE id = ? AND user_id = ?',
                 ('Cancelled', booking_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Booking cancelled successfully!', 'info')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
