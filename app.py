from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime
import os
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.rest import Client
from config import Config
from model import predict_arrival

app = Flask(__name__)
app.config.from_object(Config)
BASE_DIR = Config.BASE_DIR
DATABASE = Config.DATABASE_PATH


def get_db():
    conn = sqlite3.connect(DATABASE, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 15000")
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id TEXT UNIQUE NOT NULL,
            username TEXT,
            bus_number TEXT NOT NULL,
            bus_name TEXT,
            from_location TEXT,
            to_location TEXT,
            travel_date TEXT,
            travel_time TEXT,
            seat_number TEXT,
            passenger_name TEXT,
            passenger_age INTEGER,
            passenger_contact TEXT,
            fare REAL,
            ticket_token TEXT,
            status TEXT DEFAULT 'Confirmed',
            created_at TEXT
        )
    """)

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS fleet (
            bus_number TEXT PRIMARY KEY, bus_name TEXT NOT NULL,
            bus_type TEXT NOT NULL DEFAULT 'Volvo', ac INTEGER NOT NULL DEFAULT 1,
            layout TEXT NOT NULL DEFAULT 'Sleeper', capacity INTEGER NOT NULL DEFAULT 36,
            active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, bus_number TEXT NOT NULL,
            from_location TEXT NOT NULL, to_location TEXT NOT NULL,
            stops TEXT NOT NULL DEFAULT '', boarding_time TEXT NOT NULL,
            base_fare REAL NOT NULL DEFAULT 0, UNIQUE(bus_number, from_location, to_location)
        );
        CREATE TABLE IF NOT EXISTS bus_locations (
            bus_number TEXT PRIMARY KEY, latitude REAL NOT NULL, longitude REAL NOT NULL,
            updated_at TEXT NOT NULL, trip_status TEXT NOT NULL DEFAULT 'Idle'
        );
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending', created_at TEXT NOT NULL
        );
    """)

    cols = [row[1] for row in conn.execute(
        "PRAGMA table_info(bookings)"
    ).fetchall()]

    if "username" not in cols:
        conn.execute("ALTER TABLE bookings ADD COLUMN username TEXT")
    if "ticket_token" not in cols:
        conn.execute("ALTER TABLE bookings ADD COLUMN ticket_token TEXT")

    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_bookings_bus_date_status
            ON bookings(bus_number, travel_date, status);
        CREATE INDEX IF NOT EXISTS idx_bookings_username_created
            ON bookings(username, created_at);
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return send_from_directory(str(BASE_DIR), "index.html")


# ---------------- PREDICTION API ----------------

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(force=True)

        distance = float(data.get("distance", 0))
        traffic = float(data.get("traffic", 0))
        weather = float(data.get("weather", 0))
        previous_time = float(data.get("previous_time", 0))

        result = predict_arrival(
            distance,
            traffic,
            weather,
            previous_time
        )

        predicted_time = round(float(result), 2)

        return jsonify({
            "success": True,
            "predicted_time": predicted_time,
            "prediction": predicted_time
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


# ---------------- AI CHATBOT API ----------------

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        message = str(data.get("message", "")).strip().lower()

        if not message:
            return jsonify({
                "success": False,
                "reply": "Please enter a question."
            }), 400

        if message in [
            "hi", "hello", "hey", "hai",
            "good morning", "good afternoon", "good evening"
        ]:
            reply = (
                "Hi! 👋 Welcome to the AI Bus Arrival Prediction System. "
                "How can I help you today?"
            )

        elif (
            "what is this project" in message
            or "explain the project" in message
            or "about the project" in message
        ):
            reply = (
                "This is an AI Bus Arrival Prediction System. "
                "It predicts the estimated arrival time of buses using "
                "distance, traffic level, weather conditions, and previous travel-time data."
            )

        elif (
            "how does the prediction work" in message
            or "how prediction works" in message
            or "how does it work" in message
        ):
            reply = (
                "The system uses a Machine Learning model to predict bus arrival time. "
                "Distance, traffic, weather, and previous travel time are used as inputs "
                "to generate the estimated arrival time."
            )

        elif "what is eta" in message or "meaning of eta" in message:
            reply = (
                "ETA means Estimated Time of Arrival. "
                "It indicates approximately how long a bus may take to arrive."
            )

        elif (
            "what technology" in message
            or "technologies used" in message
            or "technology used" in message
        ):
            reply = (
                "This project uses HTML, CSS, JavaScript, Python Flask, "
                "SQLite, Leaflet/OpenStreetMap, and Machine Learning with scikit-learn."
            )

        elif "what is flask" in message:
            reply = (
                "Flask is a lightweight Python web framework used to build "
                "the backend and API services of this project."
            )

        elif (
            "what is machine learning" in message
            or "what is ml" in message
        ):
            reply = (
                "Machine Learning allows a computer system to learn patterns "
                "from data and use them to make predictions."
            )

        elif "what is random forest" in message:
            reply = (
                "Random Forest is a Machine Learning algorithm that combines "
                "multiple decision trees to make predictions."
            )

        elif "how many buses" in message or "total buses" in message:
            reply = "The system currently contains information for 25 buses."

        elif "running buses" in message or "how many buses are running" in message:
            reply = "The dashboard currently shows 22 running buses."

        elif "bus location" in message or "where is the bus" in message:
            reply = (
                "Please provide a bus number such as B001, B006, or B025 "
                "to check its available location information."
            )

        elif "what is traffic" in message or "traffic level" in message:
            reply = (
                "Traffic level represents the amount of road congestion. "
                "Higher traffic can increase the expected bus arrival time."
            )

        elif (
            "how to book" in message
            or "how can i book" in message
            or "bus booking" in message
        ):
            reply = (
                "To book a bus, open the Bus Booking section, select your route, "
                "enter the passenger details, choose an available seat, and confirm the booking."
            )

        elif "cancel booking" in message or "how to cancel" in message:
            reply = (
                "You can cancel a confirmed booking from the booking section "
                "using its booking ID."
            )

        elif (
            "live map" in message
            or "track bus" in message
        ):
            reply = (
                "The Live Map displays bus locations and route information "
                "using the map module."
            )

        elif (
            "prediction page" in message
            or "predict eta" in message
            or "predict arrival" in message
        ):
            reply = (
                "Open the Prediction page, enter a valid bus number such as B001, "
                "and select Predict ETA to get the estimated arrival time."
            )

        elif "reports" in message or "report page" in message:
            reply = (
                "The Reports section provides information about buses, "
                "running status, predictions, and system activity."
            )

        elif message in ["help", "help me", "what can you do"]:
            reply = (
                "I can help you with bus locations, ETA prediction, traffic, "
                "routes, booking, Live Map, Reports, Machine Learning, "
                "and information about this project."
            )

        elif message in ["thanks", "thank you", "thankyou"]:
            reply = "You're welcome! 😊 I'm happy to help."

        elif message in ["bye", "goodbye", "see you"]:
            reply = "Goodbye! 👋 Have a great day."

        else:
            reply = (
                "I'm here to help with the AI Bus Arrival Prediction System. "
                "You can ask me about buses, ETA, traffic, routes, booking, "
                "Live Map, Reports, Machine Learning, or the project."
            )

        return jsonify({
            "success": True,
            "reply": reply
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "reply": "Sorry, I could not process your question.",
            "error": str(e)
        }), 500


# ---------------- SIGNUP ----------------

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json(force=True)

    full_name = str(data.get("full_name", "")).strip()
    username = str(data.get("username", "")).strip().lower()
    email = str(data.get("email", "")).strip().lower()
    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))

    if not full_name or not username or not email or not password:
        return jsonify({
            "success": False,
            "message": "Please fill all required fields."
        }), 400

    if len(password) < 4:
        return jsonify({
            "success": False,
            "message": "Password must contain at least 4 characters."
        }), 400

    conn = get_db()

    try:
        conn.execute("""
            INSERT INTO users
            (full_name, username, email, phone, password_hash, role, created_at)
            VALUES (?, ?, ?, ?, ?, 'user', ?)
        """, (
            full_name,
            username,
            email,
            phone,
            generate_password_hash(password),
            datetime.now().isoformat(timespec="seconds")
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Registration successful. You can login now."
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "Username or email already exists."
        }), 409

    finally:
        conn.close()


# ---------------- LOGIN ----------------

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)

    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", ""))

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()

    if not user and username == "user" and password == "1234":
        conn = get_db()

        conn.execute("""
            INSERT OR IGNORE INTO users
            (full_name, username, email, phone, password_hash, role, created_at)
            VALUES (?, ?, ?, ?, ?, 'user', ?)
        """, (
            "Demo User",
            "user",
            "demo@example.com",
            "",
            generate_password_hash("1234"),
            datetime.now().isoformat(timespec="seconds")
        ))

        conn.commit()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

    if not user or not check_password_hash(
        user["password_hash"], password
    ):
        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401

    return jsonify({
        "success": True,
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    })


# ---------------- CREATE BOOKING ----------------

@app.route("/api/bookings", methods=["POST"])
def create_booking():
    data = request.get_json(force=True)

    required = ["booking_id", "bus_number", "seat_number"]

    if any(not data.get(k) for k in required):
        return jsonify({
            "success": False,
            "message": "Missing booking details."
        }), 400

    booking_id = str(data["booking_id"])
    bus_number = str(data["bus_number"])
    seat_number = str(data["seat_number"])
    travel_date = str(data.get("travel_date", ""))
    ticket_token = secrets.token_urlsafe(24)
    username = str(data.get("username", "")).strip().lower()

    conn = get_db()

    try:
        duplicate = conn.execute("""
            SELECT 1 FROM bookings
            WHERE bus_number = ?
            AND travel_date = ?
            AND seat_number = ?
            AND status = 'Confirmed'
        """, (
            bus_number,
            travel_date,
            seat_number
        )).fetchone()

        if duplicate:
            return jsonify({
                "success": False,
                "message": "That seat is already booked."
            }), 409

        conn.execute("""
            INSERT INTO bookings
            (booking_id, username, bus_number, bus_name,
             from_location, to_location, travel_date,
             travel_time, seat_number, passenger_name,
             passenger_age, passenger_contact, fare, ticket_token,
             status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', ?)
        """, (
            booking_id,
            username,
            bus_number,
            data.get("bus_name", ""),
            data.get("from_location", ""),
            data.get("to_location", ""),
            travel_date,
            data.get("travel_time", ""),
            seat_number,
            data.get("passenger_name", ""),
            data.get("passenger_age"),
            data.get("passenger_contact", ""),
            data.get("fare", 0),
            ticket_token,
            datetime.now().isoformat(timespec="seconds")
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Booking saved to SQLite.",
            "ticket_token": ticket_token
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "Booking ID already exists."
        }), 409

    finally:
        conn.close()


@app.route("/api/occupancy")
def occupancy_api():
    travel_date = request.args.get("date", "")
    if not travel_date:
        return jsonify({"success": False, "message": "Travel date is required."}), 400
    try:
        weekday = datetime.strptime(travel_date, "%Y-%m-%d").weekday()
    except ValueError:
        return jsonify({"success": False, "message": "Invalid travel date."}), 400
    conn = get_db()
    fleet = {r["bus_number"]: r["capacity"] for r in conn.execute("SELECT bus_number,capacity FROM fleet")}
    current = conn.execute("""SELECT bus_number,COUNT(*) AS n FROM bookings
        WHERE travel_date=? AND status='Confirmed' GROUP BY bus_number""", (travel_date,)).fetchall()
    historical = conn.execute("""SELECT bus_number,travel_date,COUNT(*) AS n FROM bookings
        WHERE status='Confirmed' AND travel_date<>? GROUP BY bus_number,travel_date""", (travel_date,)).fetchall()
    conn.close()
    by_bus = {}
    for row in historical:
        try:
            if datetime.strptime(row["travel_date"], "%Y-%m-%d").weekday() == weekday:
                by_bus.setdefault(row["bus_number"], []).append(row["n"])
        except (TypeError, ValueError):
            continue
    result = {}
    for row in current:
        by_bus.setdefault(row["bus_number"], [])
        by_bus[row["bus_number"]].append(row["n"])
    for bus, counts in by_bus.items():
        capacity = int(fleet.get(bus, 20) or 20)
        booked = next((r["n"] for r in current if r["bus_number"] == bus), 0)
        projection = min(capacity, round(sum(counts) / len(counts))) if counts else booked
        result[bus] = {"capacity": capacity, "booked": booked, "predicted": max(booked, projection),
                       "percent": round(max(booked, projection) * 100 / capacity)}
    return jsonify(result)


@app.route("/api/tickets/verify", methods=["GET", "POST"])
def verify_ticket():
    data = request.get_json(silent=True) or {}
    token = str(request.args.get("token") or data.get("token", "")).strip()
    if not token:
        return jsonify({"valid": False, "message": "Ticket token is required."}), 400
    conn = get_db()
    row = conn.execute("SELECT booking_id,bus_number,bus_name,from_location,to_location,travel_date,travel_time,seat_number,passenger_name,status FROM bookings WHERE ticket_token=?", (token,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"valid": False, "message": "Ticket not found."}), 404
    ticket = dict(row)
    ticket["valid"] = ticket["status"] == "Confirmed"
    ticket["message"] = "Valid ticket." if ticket["valid"] else "Ticket was cancelled."
    return jsonify(ticket)


@app.route("/api/notifications/send", methods=["POST"])
def send_notification():
    data = request.get_json(force=True)
    channel = str(data.get("channel", "")).lower()
    to = str(data.get("to", "")).strip()
    body = str(data.get("body", "")).strip()
    sid, token = os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN")
    sender = os.environ.get("TWILIO_WHATSAPP_FROM" if channel == "whatsapp" else "TWILIO_SMS_FROM")
    if channel not in ("whatsapp", "sms") or not to or not body:
        return jsonify({"success": False, "message": "Provide a channel, recipient and message."}), 400
    if not sid or not token or not sender:
        return jsonify({"success": False, "demo": True, "message": "Twilio is not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and the matching sender number."}), 503
    recipient = "whatsapp:" + to if channel == "whatsapp" and not to.startswith("whatsapp:") else to
    sender = "whatsapp:" + sender if channel == "whatsapp" and not sender.startswith("whatsapp:") else sender
    try:
        message = Client(sid, token).messages.create(to=recipient, from_=sender, body=body)
        return jsonify({"success": True, "message": "Alert sent via Twilio.", "sid": message.sid})
    except Exception as error:
        return jsonify({"success": False, "message": "Twilio could not send the alert.", "detail": str(error)}), 502


# ---------------- FLEET, ROUTES, DRIVER TRACKING ----------------

@app.route("/api/fleet", methods=["GET", "POST"])
def fleet_api():
    conn = get_db()
    if request.method == "GET":
        rows = conn.execute("SELECT * FROM fleet ORDER BY bus_number").fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows])
    data = request.get_json(force=True)
    number = str(data.get("bus_number", "")).strip().upper()
    name = str(data.get("bus_name", "")).strip()
    if not number or not name:
        conn.close()
        return jsonify({"success": False, "message": "Bus number and name are required."}), 400
    try:
        conn.execute("""INSERT INTO fleet(bus_number,bus_name,bus_type,ac,layout,capacity,created_at)
            VALUES(?,?,?,?,?,?,?)""", (number, name, data.get("bus_type", "Volvo"),
            1 if data.get("ac", True) else 0, data.get("layout", "Sleeper"),
            max(1, min(int(data.get("capacity", 36)), 100)), datetime.now().isoformat(timespec="seconds")))
        conn.commit()
        return jsonify({"success": True, "message": "Bus added to fleet."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "That bus number already exists."}), 409
    finally:
        conn.close()


@app.route("/api/routes", methods=["GET", "POST"])
def routes_api():
    conn = get_db()
    if request.method == "GET":
        rows = conn.execute("SELECT * FROM routes ORDER BY id DESC").fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows])
    data = request.get_json(force=True)
    required = ["bus_number", "from_location", "to_location", "boarding_time"]
    if any(not str(data.get(key, "")).strip() for key in required):
        conn.close()
        return jsonify({"success": False, "message": "Bus, origin, destination and boarding time are required."}), 400
    try:
        conn.execute("""INSERT INTO routes(bus_number,from_location,to_location,stops,boarding_time,base_fare)
            VALUES(?,?,?,?,?,?)""", (str(data["bus_number"]).strip().upper(), str(data["from_location"]).strip(),
            str(data["to_location"]).strip(), str(data.get("stops", "")).strip(),
            str(data["boarding_time"]).strip(), max(0, float(data.get("base_fare", 0)))))
        conn.commit()
        return jsonify({"success": True, "message": "Route saved."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "This bus already has that route."}), 409
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Fare must be a valid non-negative number."}), 400
    finally:
        conn.close()


@app.route("/api/driver/location", methods=["POST"])
def driver_location():
    data = request.get_json(force=True)
    try:
        bus = str(data.get("bus_number", "")).strip().upper()
        lat, lng = float(data["latitude"]), float(data["longitude"])
        if not bus or not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError("Invalid bus number or GPS coordinates.")
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"success": False, "message": str(error) or "Invalid GPS coordinates."}), 400
    conn = get_db()
    conn.execute("""INSERT INTO bus_locations(bus_number,latitude,longitude,updated_at,trip_status)
        VALUES(?,?,?,?, 'Running') ON CONFLICT(bus_number) DO UPDATE SET latitude=excluded.latitude,
        longitude=excluded.longitude,updated_at=excluded.updated_at,
        trip_status=CASE WHEN bus_locations.trip_status='Idle' THEN 'Running' ELSE bus_locations.trip_status END""",
        (bus, lat, lng, datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/driver/trip", methods=["POST"])
def driver_trip():
    data = request.get_json(force=True)
    bus = str(data.get("bus_number", "")).strip().upper()
    status = str(data.get("status", "")).strip().title()
    if not bus or status not in ("Running", "Completed", "Idle"):
        return jsonify({"success": False, "message": "Provide a bus number and Running, Completed or Idle status."}), 400
    conn = get_db()
    conn.execute("""INSERT INTO bus_locations(bus_number,latitude,longitude,updated_at,trip_status)
        VALUES(?,0,0,?,?) ON CONFLICT(bus_number) DO UPDATE SET trip_status=excluded.trip_status,updated_at=excluded.updated_at""",
        (bus, datetime.now().isoformat(timespec="seconds"), status))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": status})


@app.route("/api/analytics")
def analytics():
    conn = get_db()
    result = conn.execute("""SELECT COUNT(*) AS bookings,
        COALESCE(SUM(CASE WHEN status='Confirmed' THEN fare ELSE 0 END),0) AS revenue,
        COALESCE(SUM(CASE WHEN status='Confirmed' THEN 1 ELSE 0 END),0) AS confirmed
        FROM bookings""").fetchone()
    conn.close()
    return jsonify(dict(result))


@app.route("/api/operators", methods=["GET", "POST"])
def operators_api():
    conn = get_db()
    if request.method == "POST":
        data = request.get_json(force=True)
        name, email = str(data.get("name", "")).strip(), str(data.get("email", "")).strip()
        if not name or "@" not in email:
            conn.close()
            return jsonify({"success": False, "message": "Enter an operator name and valid email."}), 400
        conn.execute("INSERT INTO operators(name,email,created_at) VALUES(?,?,?)",
                     (name, email, datetime.now().isoformat(timespec="seconds")))
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 201
    rows = conn.execute("SELECT * FROM operators ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/operators/<int:operator_id>/approve", methods=["POST"])
def approve_operator(operator_id):
    conn = get_db()
    cur = conn.execute("UPDATE operators SET status='Approved' WHERE id=?", (operator_id,))
    conn.commit()
    conn.close()
    return (jsonify({"success": True}) if cur.rowcount else
            (jsonify({"success": False, "message": "Operator not found."}), 404))


# ---------------- GET BOOKINGS ----------------

@app.route("/api/bookings", methods=["GET"])
def get_bookings():
    username = request.args.get(
        "username", ""
    ).strip().lower()

    conn = get_db()

    if username:
        rows = conn.execute(
            "SELECT * FROM bookings WHERE username = ? ORDER BY id DESC",
            (username,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM bookings ORDER BY id DESC"
        ).fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])


# ---------------- CANCEL BOOKING ----------------

@app.route("/api/bookings/<booking_id>", methods=["DELETE"])
def cancel_booking(booking_id):
    conn = get_db()

    cur = conn.execute(
        "UPDATE bookings SET status = 'Cancelled' WHERE booking_id = ?",
        (booking_id,)
    )

    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        return jsonify({
            "success": False,
            "message": "Booking not found."
        }), 404

    return jsonify({
        "success": True,
        "message": "Booking cancelled."
    })


if __name__ == "__main__":
    init_db()
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
