from flask import Flask, render_template, request, redirect, session, jsonify

from werkzeug.security import generate_password_hash, check_password_hash

from functools import wraps

from datetime import datetime, date

import math

import os

import base64



from database import get_db_connection





app = Flask(__name__)



app.secret_key = "SST_school_bus_secret_key_change_this"





# =========================================================

# LOGIN REQUIRED

# =========================================================



def login_required(function):



    @wraps(function)

    def wrapper(*args, **kwargs):



        if "user_id" not in session:

            return redirect("/login")



        return function(*args, **kwargs)



    return wrapper





# =========================================================

# ROLE REQUIRED

# =========================================================



def role_required(*roles):



    def decorator(function):



        @wraps(function)

        def wrapper(*args, **kwargs):



            if "user_id" not in session:

                return redirect("/login")



            if session.get("role") not in roles:

                return "Access denied", 403



            return function(*args, **kwargs)



        return wrapper



    return decorator





# =========================================================

# NOTIFICATION FUNCTION

# =========================================================



def create_notification(user_id, title, message, notification_type):



    db = get_db_connection()

    cursor = db.cursor()



    cursor.execute(

        """

        INSERT INTO notifications

        (user_id, title, message, notification_type)

        VALUES (%s, %s, %s, %s)

        """,

        (user_id, title, message, notification_type)

    )



    db.commit()



    cursor.close()

    db.close()





# =========================================================

# HOME

# =========================================================



@app.route("/")

def home():



    if "user_id" in session:

        return redirect("/dashboard")



    return redirect("/login")





# =========================================================

# REGISTER

# =========================================================



@app.route("/register", methods=["GET", "POST"])

def register():



    if request.method == "POST":



        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        role = request.form["role"]



        if role not in ["parent", "driver", "student"]:

            return render_template(

                "register.html",

                error="Invalid account type."

            )



        hashed_password = generate_password_hash(password)



        db = get_db_connection()

        cursor = db.cursor()



        try:



            cursor.execute(

                """

                INSERT INTO users

                (name, email, password, role)

                VALUES (%s, %s, %s, %s)

                """,

                (name, email, hashed_password, role)

            )



            db.commit()



        except Exception:



            db.rollback()



            cursor.close()

            db.close()



            return render_template(

                "register.html",

                error="Email already exists."

            )



        cursor.close()

        db.close()



        return redirect("/login")



    return render_template("register.html")





# =========================================================

# LOGIN

# =========================================================



@app.route("/login", methods=["GET", "POST"])

def login():



    if request.method == "POST":



        email = request.form["email"]

        password = request.form["password"]



        db = get_db_connection()

        cursor = db.cursor(dictionary=True)



        cursor.execute(

            "SELECT * FROM users WHERE email=%s",

            (email,)

        )



        user = cursor.fetchone()



        cursor.close()

        db.close()



        if user and check_password_hash(

            user["password"],

            password

        ):



            session["user_id"] = user["user_id"]

            session["name"] = user["name"]

            session["role"] = user["role"]



            return redirect("/dashboard")



        return render_template(

            "login.html",

            error="Invalid email or password."

        )



    return render_template("login.html")





# =========================================================

# LOGOUT

# =========================================================



@app.route("/logout")

def logout():



    session.clear()



    return redirect("/login")





# =========================================================

# MAIN DASHBOARD

# =========================================================



@app.route("/dashboard")

@login_required

def dashboard():



    role = session["role"]



    db = get_db_connection()

    cursor = db.cursor(dictionary=True)



    data = {}



    # -----------------------------------------------------

    # ADMIN DATA

    # -----------------------------------------------------



    if role == "admin":



        cursor.execute("SELECT COUNT(*) AS total FROM users")

        data["users"] = cursor.fetchone()["total"]



        cursor.execute(

            "SELECT COUNT(*) AS total FROM students"

        )

        data["students"] = cursor.fetchone()["total"]



        cursor.execute(

            "SELECT COUNT(*) AS total FROM buses"

        )

        data["buses"] = cursor.fetchone()["total"]



        cursor.execute(

            "SELECT COUNT(*) AS total FROM routes"

        )

        data["routes"] = cursor.fetchone()["total"]



        cursor.execute(

            """

            SELECT user_id, name, email

            FROM users

            WHERE role='driver'

            """

        )



        data["drivers"] = cursor.fetchall()



        cursor.execute(

            """

            SELECT bus_id, bus_number, driver_id,

                   capacity, status

            FROM buses

            ORDER BY bus_id DESC

            """

        )



        data["bus_list"] = cursor.fetchall()



        cursor.execute(

            """

            SELECT s.student_id,

                   s.roll_number,

                   s.class_name,

                   u.name AS student_name,

                   s.parent_id,

                   s.bus_id,

                   s.pickup_point,

                   s.drop_point

            FROM students s

            JOIN users u

            ON s.user_id = u.user_id

            ORDER BY s.student_id DESC

            """

        )



        data["student_list"] = cursor.fetchall()



        cursor.execute(

            """

            SELECT user_id, name, email, role

            FROM users

            ORDER BY user_id DESC

            """

        )



        data["user_list"] = cursor.fetchall()



    # -----------------------------------------------------

    # PARENT DATA

    # -----------------------------------------------------



    elif role == "parent":



        cursor.execute(

            """

            SELECT

                s.student_id,

                s.roll_number,

                s.class_name,

                u.name AS student_name,

                s.bus_id,

                s.pickup_point,

                s.drop_point,

                b.bus_number,

                b.current_lat,

                b.current_lng

            FROM students s

            JOIN users u

                ON s.user_id = u.user_id

            LEFT JOIN buses b

                ON s.bus_id = b.bus_id

            WHERE s.parent_id=%s

            """,

            (session["user_id"],)

        )



        data["children"] = cursor.fetchall()



        cursor.execute(

            """

            SELECT title, message,

                   notification_type, created_at

            FROM notifications

            WHERE user_id=%s

            ORDER BY created_at DESC

            LIMIT 10

            """,

            (session["user_id"],)

        )



        data["notifications"] = cursor.fetchall()



    # -----------------------------------------------------

    # DRIVER DATA

    # -----------------------------------------------------



    elif role == "driver":



        cursor.execute(

            """

            SELECT *

            FROM buses

            WHERE driver_id=%s

            """,

            (session["user_id"],)

        )



        data["driver_buses"] = cursor.fetchall()



        if data["driver_buses"]:



            bus_id = data["driver_buses"][0]["bus_id"]



            cursor.execute(

                """

                SELECT

                    s.student_id,

                    s.roll_number,

                    s.class_name,

                    u.name AS student_name,

                    s.pickup_point,

                    s.drop_point

                FROM students s

                JOIN users u

                    ON s.user_id=u.user_id

                WHERE s.bus_id=%s

                """,

                (bus_id,)

            )



            data["students"] = cursor.fetchall()



    # -----------------------------------------------------

    # STUDENT DATA

    # -----------------------------------------------------



    elif role == "student":



        cursor.execute(

            """

            SELECT

                s.*,

                b.bus_number,

                b.current_lat,

                b.current_lng

            FROM students s

            LEFT JOIN buses b

                ON s.bus_id=b.bus_id

            WHERE s.user_id=%s

            """,

            (session["user_id"],)

        )



        data["student"] = cursor.fetchone()



    cursor.close()

    db.close()



    return render_template(

        "dashboard.html",

        name=session["name"],

        role=role,

        data=data

    )





# =========================================================

# ADMIN - ADD BUS

# =========================================================



@app.route("/admin/add-bus", methods=["POST"])

@role_required("admin")

def add_bus():



    bus_number = request.form["bus_number"]

    capacity = request.form["capacity"]

    driver_id = request.form.get("driver_id") or None



    db = get_db_connection()

    cursor = db.cursor()



    cursor.execute(

        """

        INSERT INTO buses

        (bus_number, driver_id, capacity, status)

        VALUES (%s, %s, %s, 'Active')

        """,

        (bus_number, driver_id, capacity)

    )



    db.commit()



    cursor.close()

    db.close()



    return redirect("/dashboard")





# =========================================================

# ADMIN - ADD STUDENT RECORD

# =========================================================



@app.route("/admin/add-student", methods=["POST"])

@role_required("admin")

def add_student():



    user_id = request.form["user_id"]

    roll_number = request.form["roll_number"]

    class_name = request.form["class_name"]

    parent_id = request.form.get("parent_id") or None

    bus_id = request.form.get("bus_id") or None

    pickup_point = request.form["pickup_point"]

    drop_point = request.form["drop_point"]



    pickup_lat = request.form.get("pickup_lat") or None

    pickup_lng = request.form.get("pickup_lng") or None

    drop_lat = request.form.get("drop_lat") or None

    drop_lng = request.form.get("drop_lng") or None



    db = get_db_connection()

    cursor = db.cursor()



    cursor.execute(

        """

        INSERT INTO students

        (

            user_id,

            roll_number,

            class_name,

            parent_id,

            bus_id,

            pickup_point,

            drop_point,

            pickup_lat,

            pickup_lng,

            drop_lat,

            drop_lng

        )

        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)

        """,

        (

            user_id,

            roll_number,

            class_name,

            parent_id,

            bus_id,

            pickup_point,

            drop_point,

            pickup_lat,

            pickup_lng,

            drop_lat,

            drop_lng

        )

    )



    db.commit()



    cursor.close()

    db.close()



    return redirect("/dashboard")





# =========================================================

# ADMIN - ASSIGN STUDENT TO BUS

# =========================================================



@app.route("/admin/assign-bus", methods=["POST"])

@role_required("admin")

def assign_bus():



    student_id = request.form["student_id"]

    bus_id = request.form["bus_id"]



    db = get_db_connection()

    cursor = db.cursor(dictionary=True)



    cursor.execute(

        """

        UPDATE students

        SET bus_id=%s

        WHERE student_id=%s

        """,

        (bus_id, student_id)

    )



    db.commit()



    cursor.execute(

        """

        SELECT parent_id

        FROM students

        WHERE student_id=%s

        """,

        (student_id,)

    )



    student = cursor.fetchone()



    if student and student["parent_id"]:



        create_notification(

            student["parent_id"],

            "Bus Allocation",

            "Your child has been assigned to a bus.",

            "Bus Allocation"

        )



    cursor.close()

    db.close()



    return redirect("/dashboard")





# =========================================================

# DRIVER - MARK BOARDING

# =========================================================



@app.route("/driver/board", methods=["POST"])

@role_required("driver")

def board_student():



    student_id = request.form["student_id"]

    bus_id = request.form["bus_id"]



    db = get_db_connection()

    cursor = db.cursor(dictionary=True)



    cursor.execute(

        """

        INSERT INTO bus_attendance

        (

            student_id,

            bus_id,

            boarding_time,

            status

        )

        VALUES (%s,%s,NOW(),'Boarded')

        """,

        (student_id, bus_id)

    )



    db.commit()



    cursor.execute(

        """

        SELECT parent_id

        FROM students

        WHERE student_id=%s

        """,

        (student_id,)

    )



    student = cursor.fetchone()



    if student and student["parent_id"]:



        create_notification(

            student["parent_id"],

            "Student Boarded",

            "Your child has boarded the school bus.",

            "Attendance"

        )



    cursor.close()

    db.close()



    return redirect("/dashboard")





# =========================================================

# DRIVER - MARK DROP

# =========================================================



@app.route("/driver/drop", methods=["POST"])

@role_required("driver")

def drop_student():



    student_id = request.form["student_id"]

    bus_id = request.form["bus_id"]



    db = get_db_connection()

    cursor = db.cursor(dictionary=True)



    cursor.execute(

        """

        SELECT attendance_id

        FROM bus_attendance

        WHERE student_id=%s

        AND bus_id=%s

        AND DATE(boarding_time)=CURDATE()

        AND exit_time IS NULL

        ORDER BY attendance_id DESC

        LIMIT 1

        """,

        (student_id, bus_id)

    )



    attendance = cursor.fetchone()



    if attendance:



        cursor.execute(

            """

            UPDATE bus_attendance

            SET exit_time=NOW(),

                status='Dropped'

            WHERE attendance_id=%s

            """,

            (attendance["attendance_id"],)

        )



        db.commit()



    cursor.execute(

        """

        SELECT parent_id

        FROM students

        WHERE student_id=%s

        """,

        (student_id,)

    )



    student = cursor.fetchone()



    if student and student["parent_id"]:



        create_notification(

            student["parent_id"],

            "Student Dropped",

            "Your child has reached the drop point.",

            "Attendance"

        )



    cursor.close()

    db.close()



    return redirect("/dashboard")





# =========================================================

# DRIVER - UPDATE LIVE LOCATION

# =========================================================



@app.route("/api/location", methods=["POST"])

@login_required

def update_location():



    if session["role"] != "driver":

        return jsonify({

            "error": "Only drivers can update bus location"

        }), 403



    data = request.get_json()



    latitude = data.get("latitude")

    longitude = data.get("longitude")



    if latitude is None or longitude is None:

        return jsonify({

            "error": "Location missing"

        }), 400



    db = get_db_connection()

    cursor = db.cursor(dictionary=True)



    cursor.execute(

        """

        SELECT bus_id

        FROM buses

        WHERE driver_id=%s

        LIMIT 1

        """,

        (session["user_id"],)

    )



    bus = cursor.fetchone()



    if not bus:



        cursor.close()

        db.close()



        return jsonify({

            "error": "No bus assigned"

        }), 404



    bus_id = bus["bus_id"]



    cursor.execute(

        """

        INSERT INTO bus_tracking

        (bus_id, latitude, longitude)

        VALUES (%s,%s,%s)

        """,

        (bus_id, latitude, longitude)

    )



    cursor.execute(

        """

        UPDATE buses

        SET current_lat=%s,

            current_lng=%s,

            last_location_update=NOW()

        WHERE bus_id=%s

        """,

        (latitude, longitude, bus_id)

    )



    db.commit()



    cursor.close()

    db.close()



    return jsonify({

        "success": True,

        "bus_id": bus_id,

        "latitude": latitude,

        "longitude": longitude

    })





# =========================================================

# =========================================================
# GET BUS LOCATION
# =========================================================

@app.route("/api/bus/<int:bus_id>/location")
@login_required
def get_bus_location(bus_id):

    role = session.get("role")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if role == "parent":

        cursor.execute("""
            SELECT 1
            FROM students
            WHERE parent_id=%s
              AND bus_id=%s
            LIMIT 1
        """, (session["user_id"], bus_id))

        allowed = cursor.fetchone()

    elif role == "driver":

        cursor.execute("""
            SELECT 1
            FROM buses
            WHERE bus_id=%s
              AND driver_id=%s
            LIMIT 1
        """, (bus_id, session["user_id"]))

        allowed = cursor.fetchone()

    elif role == "admin":

        allowed = True

    else:

        allowed = False

    if not allowed:

        cursor.close()
        db.close()

        return jsonify({
            "error": "Access denied"
        }), 403

    cursor.execute("""
        SELECT
            latitude,
            longitude,
            recorded_at
        FROM bus_tracking
        WHERE bus_id=%s
        ORDER BY tracking_id DESC
        LIMIT 1
    """, (bus_id,))

    location = cursor.fetchone()

    cursor.close()
    db.close()

    if not location:

        return jsonify({
            "available": False
        })

    return jsonify({
        "available": True,
        "latitude": float(location["latitude"]),
        "longitude": float(location["longitude"]),
        "recorded_at": str(location["recorded_at"])
    })
# NOTIFICATIONS
# =========================================================

@app.route("/notifications")
@login_required
def notifications():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM notifications
        WHERE user_id=%s
        ORDER BY created_at DESC
    """, (session["user_id"],))

    notifications_list = cursor.fetchall()

    cursor.close()
    db.close()

    if session["role"] == "driver":

        return render_template(
            "driver/notifications.html",
            notifications=notifications_list
        )

    if session["role"] == "parent":

        return render_template(
            "parent/notifications.html",
            notifications=notifications_list
        )

    return render_template(
        "notifications.html",
        notifications=notifications_list
    )
# EMERGENCY ALERT

# =========================================================



@app.route("/emergency", methods=["POST"])

@role_required("driver")

def emergency():



    bus_id = request.form["bus_id"]

    latitude = request.form.get("latitude")

    longitude = request.form.get("longitude")

    message = request.form.get(

        "message",

        "Emergency alert from school bus."

    )



    db = get_db_connection()

    cursor = db.cursor(dictionary=True)



    cursor.execute(

        """

        INSERT INTO emergency_alerts

        (

            bus_id,

            driver_id,

            latitude,

            longitude,

            message

        )

        VALUES (%s,%s,%s,%s,%s)

        """,

        (

            bus_id,

            session["user_id"],

            latitude,

            longitude,

            message

        )

    )



    db.commit()



    # Notify all admins

    cursor.execute(

        """

        SELECT user_id

        FROM users

        WHERE role='admin'

        """

    )



    admins = cursor.fetchall()



    for admin in admins:



        create_notification(

            admin["user_id"],

            "EMERGENCY ALERT",

            message,

            "Emergency"

        )



    # Notify parents of students on bus

    cursor.execute(

        """

        SELECT parent_id

        FROM students

        WHERE bus_id=%s

        AND parent_id IS NOT NULL

        """,

        (bus_id,)

    )



    parents = cursor.fetchall()



    for parent in parents:



        create_notification(

            parent["parent_id"],

            "Bus Emergency Alert",

            message,

            "Emergency"

        )



    cursor.close()

    db.close()



    return redirect("/dashboard")





# =========================================================

# ROUTE OPTIMIZATION

# =========================================================



def distance(point1, point2):



    lat1, lon1 = point1

    lat2, lon2 = point2



    return math.sqrt(

        (lat1 - lat2) ** 2 +

        (lon1 - lon2) ** 2

    )





def nearest_neighbor(points):



    if not points:

        return []



    remaining = points.copy()



    route = [remaining.pop(0)]



    while remaining:



        current = route[-1]



        nearest = min(

            remaining,

            key=lambda point: distance(

                current,

                point

            )

        )



        route.append(nearest)



        remaining.remove(nearest)



    return route





@app.route("/admin/optimize-route", methods=["POST"])

@role_required("admin")

def optimize_route():



    bus_id = request.form["bus_id"]



    db = get_db_connection()

    cursor = db.cursor(dictionary=True)



    cursor.execute(

        """

        SELECT

            student_id,

            pickup_point,

            pickup_lat,

            pickup_lng

        FROM students

        WHERE bus_id=%s

        AND pickup_lat IS NOT NULL

        AND pickup_lng IS NOT NULL

        """,

        (bus_id,)

    )



    students = cursor.fetchall()



    if len(students) < 2:



        cursor.close()

        db.close()



        return redirect("/dashboard")



    points = []



    for student in students:



        points.append(

            (

                float(student["pickup_lat"]),

                float(student["pickup_lng"]),

                student["pickup_point"]

            )

        )



    coordinates = [

        (point[0], point[1])

        for point in points

    ]



    optimized = nearest_neighbor(coordinates)



    route_names = []



    for coordinate in optimized:



        for point in points:



            if (

                point[0] == coordinate[0]

                and point[1] == coordinate[1]

            ):



                route_names.append(point[2])



    route_text = " → ".join(route_names)



    cursor.execute(

        """

        SELECT route_id

        FROM routes

        WHERE bus_id=%s

        LIMIT 1

        """,

        (bus_id,)

    )



    route = cursor.fetchone()



    if route:



        cursor.execute(

            """

            UPDATE routes

            SET optimized_path=%s

            WHERE route_id=%s

            """,

            (route_text, route["route_id"])

        )



    else:



        cursor.execute(

            """

            INSERT INTO routes

            (

                bus_id,

                route_name,

                start_point,

                end_point,

                optimized_path

            )

            VALUES (%s,%s,%s,%s,%s)

            """,

            (

                bus_id,

                "Optimized Route",

                route_names[0],

                route_names[-1],

                route_text

            )

        )



    db.commit()



    cursor.close()

    db.close()



    return redirect("/dashboard")





# =========================================================

# =========================================================
# DRIVER - BUS DETAILS
# =========================================================

@app.route("/driver/bus")
@role_required("driver")
def driver_bus():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM buses
        WHERE driver_id=%s
        LIMIT 1
    """, (session["user_id"],))

    bus = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template("driver/bus.html", bus=bus)


# =========================================================
# DRIVER - ROUTE
# =========================================================

@app.route("/driver/route")
@role_required("driver")
def driver_route():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT r.*
        FROM routes r
        JOIN buses b ON r.bus_id=b.bus_id
        WHERE b.driver_id=%s
        LIMIT 1
    """, (session["user_id"],))

    route = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template("driver/route.html", route=route)


# =========================================================
# DRIVER - STUDENTS
# =========================================================

@app.route("/driver/students")
@role_required("driver")
def driver_students():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.student_id,
            s.roll_number,
            s.class_name,
            u.name AS student_name,
            s.pickup_point,
            s.drop_point,
            s.bus_id
        FROM students s
        JOIN users u ON s.user_id=u.user_id
        JOIN buses b ON s.bus_id=b.bus_id
        WHERE b.driver_id=%s
        ORDER BY u.name
    """, (session["user_id"],))

    students = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("driver/students.html", students=students)


# =========================================================
# DRIVER - ATTENDANCE PAGE
# =========================================================

@app.route("/driver/attendance")
@role_required("driver")
def driver_attendance():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.student_id,
            s.roll_number,
            s.class_name,
            u.name AS student_name,
            s.pickup_point,
            s.drop_point,
            s.bus_id
        FROM students s
        JOIN users u ON s.user_id=u.user_id
        JOIN buses b ON s.bus_id=b.bus_id
        WHERE b.driver_id=%s
        ORDER BY u.name
    """, (session["user_id"],))

    students = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "driver/attendance.html",
        students=students
    )


# =========================================================
# DRIVER - LOCATION PAGE
# =========================================================

@app.route("/driver/location")
@role_required("driver")
def driver_location():

    return render_template("driver/location.html")


# =========================================================
# PARENT - CHILD DETAILS
# =========================================================

@app.route("/parent/child")
@role_required("parent")
def parent_child():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.student_id,
            s.roll_number,
            s.class_name,
            u.name AS student_name,
            s.bus_id,
            s.pickup_point,
            s.drop_point
        FROM students s
        JOIN users u ON s.user_id=u.user_id
        WHERE s.parent_id=%s
        LIMIT 1
    """, (session["user_id"],))

    child = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template("parent/child.html", child=child)


# =========================================================
# PARENT - BUS DETAILS
# =========================================================

@app.route("/parent/bus")
@role_required("parent")
def parent_bus():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.*
        FROM buses b
        JOIN students s ON s.bus_id=b.bus_id
        WHERE s.parent_id=%s
        LIMIT 1
    """, (session["user_id"],))

    bus = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template("parent/bus.html", bus=bus)


# =========================================================
# PARENT - BUS LOCATION PAGE
# =========================================================

@app.route("/parent/location")
@role_required("parent")
def parent_location():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            b.bus_id,
            b.bus_number,
            b.current_lat,
            b.current_lng,
            b.last_location_update
        FROM buses b
        JOIN students s ON s.bus_id=b.bus_id
        WHERE s.parent_id=%s
        LIMIT 1
    """, (session["user_id"],))

    bus = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template("parent/location.html", bus=bus)


# =========================================================
# PARENT - ATTENDANCE
# =========================================================

@app.route("/parent/attendance")
@role_required("parent")
def parent_attendance():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            ba.attendance_id,
            ba.boarding_time,
            ba.exit_time,
            ba.status,
            b.bus_number,
            u.name AS student_name
        FROM bus_attendance ba
        JOIN students s ON ba.student_id=s.student_id
        JOIN users u ON s.user_id=u.user_id
        JOIN buses b ON ba.bus_id=b.bus_id
        WHERE s.parent_id=%s
        ORDER BY ba.attendance_id DESC
    """, (session["user_id"],))

    attendance = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "parent/attendance.html",
        attendance=attendance
    )


# =========================================================
# PARENT - BUS ACTIVITY
# =========================================================

@app.route("/parent/activity")
@role_required("parent")
def parent_activity():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            ba.activity_id,
            ba.activity_type,
            ba.description,
            ba.image_path,
            ba.created_at,
            b.bus_number
        FROM bus_activities ba
        JOIN buses b ON ba.bus_id=b.bus_id
        JOIN students s ON s.bus_id=b.bus_id
        WHERE s.parent_id=%s
        ORDER BY ba.created_at DESC
    """, (session["user_id"],))

    activities = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "parent/activity.html",
        activities=activities
    )


# =========================================================
# =========================================================
# PARENT - CAMERA
# =========================================================

@app.route("/parent/camera")
@role_required("parent")
def parent_camera():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            ba.activity_id,
            ba.activity_type,
            ba.description,
            ba.image_path,
            ba.created_at,
            b.bus_number
        FROM bus_activities ba
        JOIN buses b ON ba.bus_id=b.bus_id
        JOIN students s ON s.bus_id=b.bus_id
        WHERE s.parent_id=%s
        ORDER BY ba.created_at DESC
        LIMIT 1
    """, (session["user_id"],))

    latest_activity = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template(
        "parent/camera.html",
        latest_activity=latest_activity
    )
# PARENT - EMERGENCY ALERTS
# =========================================================

@app.route("/parent/alerts")
@role_required("parent")
def parent_alerts():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            ea.*,
            b.bus_number
        FROM emergency_alerts ea
        JOIN buses b ON ea.bus_id=b.bus_id
        JOIN students s ON s.bus_id=b.bus_id
        WHERE s.parent_id=%s
        ORDER BY ea.created_at DESC
    """, (session["user_id"],))

    alerts = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("parent/alerts.html", alerts=alerts)


# =========================================================
# =========================================================
# DRIVER - JOURNEY
# =========================================================

@app.route("/driver/journey")
@role_required("driver")
def driver_journey():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT ba.*, b.bus_number, u.name AS student_name
        FROM bus_attendance ba
        JOIN buses b ON ba.bus_id=b.bus_id
        JOIN students s ON ba.student_id=s.student_id
        JOIN users u ON s.user_id=u.user_id
        WHERE b.driver_id=%s
        ORDER BY ba.attendance_id DESC
        LIMIT 100
    """, (session["user_id"],))

    journeys = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "journey.html",
        journeys=journeys
    )


# =========================================================
# DRIVER - EMERGENCY PAGE
# =========================================================

@app.route("/driver/emergency")
@role_required("driver")
def driver_emergency():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM buses
        WHERE driver_id=%s
        LIMIT 1
    """, (session["user_id"],))

    bus = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template(
        "driver/emergency.html",
        bus=bus
    )


# =========================================================
# PARENT - JOURNEY HISTORY
# =========================================================

@app.route("/parent/journey")
@role_required("parent")
def parent_journey():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            ba.*,
            b.bus_number,
            u.name AS student_name
        FROM bus_attendance ba
        JOIN students s ON ba.student_id=s.student_id
        JOIN users u ON s.user_id=u.user_id
        JOIN buses b ON ba.bus_id=b.bus_id
        WHERE s.parent_id=%s
        ORDER BY ba.attendance_id DESC
        LIMIT 100
    """, (session["user_id"],))

    journeys = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "journey.html",
        journeys=journeys
    )
# CAMERA PAGE
# =========================================================

@app.route("/camera")
@login_required
def camera():

    role = session.get("role")

    if role == "driver":

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM buses
            WHERE driver_id=%s
            LIMIT 1
        """, (session["user_id"],))

        bus = cursor.fetchone()

        cursor.close()
        db.close()

        return render_template(
            "driver/camera.html",
            role=role,
            bus=bus
        )

    if role == "parent":

        return render_template(
            "parent/camera.html",
            role=role
        )

    if role == "admin":

        return render_template(
            "driver/camera.html",
            role=role,
            bus=None
        )

    return "Camera access denied", 403
# =========================================================
# SAVE CAMERA SNAPSHOT
# =========================================================

@app.route("/camera/snapshot", methods=["POST"])
@role_required("driver")
def save_snapshot():

    data = request.get_json(silent=True) or {}

    image_data = data.get("image")
    bus_id = data.get("bus_id")

    if not image_data or not bus_id:

        return jsonify({
            "error": "Image or bus missing"
        }), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT bus_id
        FROM buses
        WHERE bus_id=%s
          AND driver_id=%s
        LIMIT 1
    """, (bus_id, session["user_id"]))

    bus = cursor.fetchone()

    if not bus:

        cursor.close()
        db.close()

        return jsonify({
            "error": "This bus is not assigned to you"
        }), 403

    try:

        if "," in image_data:
            image_data = image_data.split(",", 1)[1]

        image_bytes = base64.b64decode(image_data)

    except Exception:

        cursor.close()
        db.close()

        return jsonify({
            "error": "Invalid image data"
        }), 400

    upload_folder = os.path.join(
        app.static_folder,
        "uploads"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    filename = (
        "bus_"
        + str(bus_id)
        + "_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".jpg"
    )

    filepath = os.path.join(
        upload_folder,
        filename
    )

    with open(filepath, "wb") as file:
        file.write(image_bytes)

    cursor.execute("""
        INSERT INTO bus_activities
        (
            bus_id,
            activity_type,
            description,
            image_path
        )
        VALUES
        (%s, 'Camera Snapshot',
         'Bus camera activity', %s)
    """, (
        bus_id,
        "uploads/" + filename
    ))

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        "success": True,
        "filename": filename
    })
# JOURNEY HISTORY

# =========================================================



@app.route("/journey/<int:student_id>")

@login_required

def journey_history(student_id):



    db = get_db_connection()

    cursor = db.cursor(dictionary=True)



    cursor.execute(

        """

        SELECT

            ba.*,

            b.bus_number

        FROM bus_attendance ba

        JOIN buses b

            ON ba.bus_id=b.bus_id

        WHERE ba.student_id=%s

        ORDER BY ba.attendance_id DESC

        """,

        (student_id,)

    )



    journeys = cursor.fetchall()



    cursor.close()

    db.close()



    return render_template(

        "journey.html",

        journeys=journeys

    )





# =========================================================

# RUN

# =========================================================



if __name__ == "__main__":

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )
