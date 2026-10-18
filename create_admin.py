from werkzeug.security import generate_password_hash
from database import get_db_connection


name = "System Admin"
email = "admin@school.com"
password = "Admin@123"
role = "admin"


hashed_password = generate_password_hash(password)


db = get_db_connection()
cursor = db.cursor()


cursor.execute(
    """
    INSERT INTO users
    (name, email, password, role)
    VALUES (%s, %s, %s, %s)
    """,
    (
        name,
        email,
        hashed_password,
        role
    )
)


db.commit()

cursor.close()
db.close()


print("Admin created successfully.")
print("Email:", email)
print("Password:", password)