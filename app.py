from flask import Flask, render_template, redirect, request, url_for, session, flash
from werkzeug.security import  generate_password_hash, check_password_hash
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = "ram ram ji"

users = []
bookings = []
booking_counter = 1



@app.route('/')
def index():
    return render_template("index.html")


# login logout pages
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = next((u for u in users if u['email'] == email), None)

        if user and check_password_hash(user['password'], password):
            session['user'] = {
                "id": user['id'],
                "name": user['name'],
                "email": user['email']
            }
            return redirect(url_for('dashboard'))

        flash("Invalid credentials", "danger")

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if any(u['email'] == email for u in users):
            flash("Email already registered", "danger")
            return redirect(url_for('signup'))

        users.append({
            "id": len(users) + 1,
            "name": name,
            "email": email,
            "password": password
        })

        flash("Registration successful. Please login.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_bookings = [b for b in bookings if b['user_id'] == session['user']['id']]
    return render_template('dashboard.html', bookings=user_bookings)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out!', 'info')
    return redirect(url_for('index'))


#main pages
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        return redirect(url_for(
            'booking',
            mode=request.form['mode'],
            source=request.form['source'],
            destination=request.form['destination'],
            price="1500"
        ))

    return render_template('search.html')

@app.route('/booking')
def booking():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template(
        'booking.html',
        mode=request.args.get('mode'),
        source=request.args.get('source'),
        destination=request.args.get('destination'),
        price=request.args.get('price')
    )



@app.route('/confirm', methods=['POST'])
def confirm():
    global booking_counter

    if 'user' not in session:
        return redirect(url_for('login'))

    booking = {
        "booking_id": booking_counter,
        "user_id": session['user']['id'],
        "mode": request.form['mode'],
        "source": request.form['source'],
        "destination": request.form['destination'],
        "price": request.form['price'],
        "status": "CONFIRMED",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    bookings.append(booking)
    booking_counter += 1

    return render_template('confirmation.html', booking=booking)

@app.route('/cancel/<int:booking_id>')
def cancel(booking_id):
    for booking in bookings:
        if booking['booking_id'] == booking_id:
            booking['status'] = "CANCELLED"
            break

    flash("Booking cancelled successfully", "warning")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)


