from flask import Flask, render_template, redirect, request, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key

# ---------------- APP SETUP ----------------

app = Flask(__name__)
app.secret_key = "ram ram ji"

# ---------------- AWS DYNAMODB SETUP ----------------


dynamodb = boto3.resource(
    'dynamodb',
    region_name='ap-south-1',  
    aws_access_key_id='TEMP_ACCESS_KEY',
    aws_secret_access_key='TEMP_SECRET_KEY',
    aws_session_token='TEMP_SESSION_TOKEN'
)

users_table = dynamodb.Table('TravelGoUsers')
bookings_table = dynamodb.Table('TravelGoBookings')

# ---------------- STATIC TRAVEL OPTIONS ----------------

travel_options = [
    {"id": 1, "mode": "Flight", "provider": "IndiGo", "source": "Delhi", "destination": "Mumbai"},
    {"id": 2, "mode": "Train", "provider": "Rajdhani Express", "source": "Delhi", "destination": "Mumbai"},
    {"id": 3, "mode": "Bus", "provider": "Volvo AC", "source": "Delhi", "destination": "Jaipur"},
    {"id": 4, "mode": "Hotel", "provider": "Taj Palace", "source": "Mumbai", "destination": "Mumbai"}
]

# ---------------- PRICE LOGIC ----------------

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

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    return render_template("index.html")

# ---------------- AUTH ----------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if users_table.get_item(Key={"email": email}).get("Item"):
            flash("Email already registered", "danger")
            return redirect(url_for('signup'))

        users_table.put_item(
            Item={
                "email": email,
                "id": int(datetime.now().timestamp()),
                "name": name,
                "password": password
            }
        )

        flash("Registration successful. Please login.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        response = users_table.get_item(Key={"email": email})
        user = response.get("Item")

        if user and check_password_hash(user['password'], password):
            session['user'] = {
                "id": user['id'],
                "name": user['name'],
                "email": user['email']
            }
            return redirect(url_for('index'))

        flash("Invalid credentials", "danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out!", "info")
    return redirect(url_for('index'))

# ---------------- SEARCH ----------------

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

            opt = option.copy()
            opt['price'] = calculate_price(mode, source, destination)
            results.append(opt)

    return render_template('results.html', results=results)

# ---------------- CONFIRM BOOKING ----------------

@app.route('/confirm', methods=['POST'])
def confirm():
    booking_id = int(datetime.now().timestamp())

    booking = {
        "booking_id": booking_id,
        "user_email": session["user"]["email"],
        "mode": request.form['mode'],
        "provider": request.form['provider'],
        "source": request.form['source'],
        "destination": request.form['destination'],
        "price": int(request.form['price']),
        "status": "CONFIRMED"
    }

    bookings_table.put_item(Item=booking)

    return render_template("confirmation.html", booking=booking)

# ---------------- DASHBOARD ----------------

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    email = session['user']['email']

    response = bookings_table.query(
        IndexName='user_email-index',
        KeyConditionExpression=Key('user_email').eq(email)
    )

    return render_template('dashboard.html', bookings=response.get("Items", []))

# ---------------- BOOKING DETAILS ----------------

@app.route('/booking-details/<int:booking_id>')
def booking_details(booking_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    response = bookings_table.get_item(Key={"booking_id": booking_id})
    booking = response.get("Item")

    if not booking or booking['user_email'] != session['user']['email']:
        flash("Booking not found", "warning")
        return redirect(url_for('dashboard'))

    return render_template('booking_details.html', booking=booking)

# ---------------- CANCEL BOOKING ----------------

@app.route('/cancel/<int:booking_id>')
def cancel(booking_id):
    bookings_table.update_item(
        Key={"booking_id": booking_id},
        UpdateExpression="SET #s = :new",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":new": "CANCELLED"}
    )

    flash("Booking cancelled successfully", "warning")
    return redirect(url_for('dashboard'))

# ---------------- RUN ----------------

if __name__ == '__main__':
    app.run(debug=True)
