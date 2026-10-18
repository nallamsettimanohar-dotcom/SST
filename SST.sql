USE school_bus_db;

-- 1. USERS
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'parent', 'driver', 'student') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. BUSES
CREATE TABLE buses (
    bus_id INT AUTO_INCREMENT PRIMARY KEY,
    bus_number VARCHAR(50) UNIQUE NOT NULL,
    driver_id INT,
    capacity INT,
    status VARCHAR(30) DEFAULT 'Active'
);

-- 3. STUDENTS
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    roll_number VARCHAR(50) UNIQUE,
    class_name VARCHAR(50),
    parent_id INT,
    bus_id INT,
    pickup_point VARCHAR(255),
    drop_point VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id)
);

-- 4. ROUTES
CREATE TABLE routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id INT,
    route_name VARCHAR(100),
    start_point VARCHAR(255),
    end_point VARCHAR(255),
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id)
);

-- 5. BUS TRACKING
CREATE TABLE bus_tracking (
    tracking_id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id INT,
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id)
);

-- 6. BUS ATTENDANCE
CREATE TABLE bus_attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    bus_id INT,
    boarding_time DATETIME,
    exit_time DATETIME,
    status VARCHAR(30),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id)
);

-- 7. BUS ACTIVITIES
CREATE TABLE bus_activities (
    activity_id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id INT,
    activity_type VARCHAR(100),
    description TEXT,
    image_path VARCHAR(255),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id)
);