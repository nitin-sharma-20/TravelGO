from flask import Flask, render_template, redirect, request, url_for, session, flash
from werkzeug.security import  generate_password_hash, check_password_hash
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = "ram ram ji"

users = []
bookings = []
booking_counter = 1
            
travel_options = [
    {
        "id": 1,
        "mode": "Flight",
        "provider": "IndiGo",
        "source": "Delhi",
        "destination": "Mumbai",
        "price": 5200
    },
    {
        "id": 2,
        "mode": "Train",
        "provider": "Rajdhani Express",
        "source": "Delhi",
        "destination": "Mumbai",
        "price": 2400
    },
    {
        "id": 3,
        "mode": "Bus",
        "provider": "Volvo AC",
        "source": "Delhi",
        "destination": "Jaipur",
        "price": 900
    },
    {
        "id": 4,
        "mode": "Hotel",
        "provider": "Taj Palace",
        "source": "Mumbai",
        "destination": "Mumbai",
        "price": 7500
    }
]

# ---------------- PRICE CALCULATION LOGIC ----------------

route_distances = {
    ("Delhi", "Mumbai"): 1400,
    ("Delhi", "Jaipur"): 280,
    ("Mumbai", "Goa"): 590,
}

def calculate_price(mode, source, destination):
    base_rate = {
        "Bus": 3,
        "Train": 2,
        "Flight": 5,
        "Hotel": 1500
    }

    if mode == "Hotel":
        return base_rate["Hotel"]

    distance = route_distances.get((source, destination), 500)
    return distance * base_rate.get(mode, 3)


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
            return redirect(url_for('index'))

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
    if "user" not in session:
        return redirect(url_for("login"))

    print("SESSION USER =", session["user"])
    print("TYPE =", type(session["user"]))
    print("ALL BOOKINGS =", bookings)

    email = session["user"]["email"]

    user_bookings = [
        b for b in bookings
        if b.get("user_email") == email
    ]

    return render_template("dashboard.html", bookings=user_bookings)





@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out!', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']['id']
    user_bookings = [b for b in bookings if b['user_id'] == user_id]

    total_bookings = len(user_bookings)
    active_bookings = sum(1 for b in user_bookings if b['status'] == 'CONFIRMED')
    last_booking_time = (
        max(b['timestamp'] for b in user_bookings)
        if user_bookings else "N/A"
    )

    return render_template(
        'profile.html',
        user=session['user'],
        total_bookings=total_bookings,
        active_bookings=active_bookings,
        last_booking_time=last_booking_time
    )



#main pages
@app.route('/search', methods=['POST'])
def search():
    if 'user' not in session:
        flash("Please login to search and book trips", "warning")
        return redirect(url_for('login'))

    mode = request.form['mode']
    source = request.form['source']
    destination = request.form['destination']

    results = []

    for option in travel_options:
        if (option['mode'].lower() == mode.lower()
            and option['source'].lower() == source.lower()
            and option['destination'].lower() == destination.lower()):

            price = calculate_price(mode, source, destination)

            opt = option.copy()
            opt['price'] = price
            results.append(opt)

    return render_template('results.html', results=results)



@app.route('/booking')
def booking():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template(
        'booking.html',
        mode=request.args.get('mode'),
        source=request.args.get('source'),
        destination=request.args.get('destination'),
        price=request.args.get('price'),
        provider=request.args.get('provider')
    )

@app.route('/booking-details/<int:booking_id>')
def booking_details(booking_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    booking = next(
        (b for b in bookings
         if b['booking_id'] == booking_id
         and b['user_email'] == session['user']['email']),
        None
    )

    if not booking:
        flash("Booking not found", "warning")
        return redirect(url_for('dashboard'))

    return render_template('booking_details.html', booking=booking)




@app.route('/confirm', methods=['POST'])
def confirm():
    booking_id = len(bookings) + 1

    mode = request.form['mode']
    provider = request.form['provider']
    source = request.form['source']
    destination = request.form['destination']
    price = request.form['price']

    booking = {
        "booking_id": booking_id,
        "user_email": session["user"]["email"],
        "mode": mode,
        "provider": provider,
        "source": source,
        "destination": destination,
        "price": price,
        "status": "CONFIRMED"
    }

    bookings.append(booking)

    return render_template("confirmation.html", booking=booking)


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


