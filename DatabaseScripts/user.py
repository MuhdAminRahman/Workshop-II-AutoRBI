# Allows user_module to communicate with the PostgreSQL database
import psycopg2
from db_connection import get_connection


# CREATE USER function
def create_user(username, password, full_name, role):
    conn = get_connection()
    if not conn:
        return

    if role not in ('Admin', 'Engineer'):
        print("Invalid role. Must be 'Admin' or 'Engineer'.")
        return

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO users (username, password, full_name, role, status)
        VALUES (%s, %s, %s, %s, 'Active')
        RETURNING user_id;
        """

        cur.execute(sql, (username, password, full_name, role))
        user_id = cur.fetchone()[0]
        conn.commit()

        print(f"User '{username}' created successfully.")
        return user_id

    except psycopg2.errors.UniqueViolation:
        print(f"Username '{username}' already exists.")
        conn.rollback()

    except Exception as e:
        print("Error creating user:", e)
        conn.rollback()

    finally:
        cur.close()
        conn.close()


# RETRIEVE USERS function
def retrieve_users():
    conn = get_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()

        sql = """
        SELECT user_id, username, full_name, role, status, created_at
        FROM users
        ORDER BY user_id;
        """

        cur.execute(sql)
        rows = cur.fetchall()

        if not rows:
            print("No users found.")
            return

        print("List of all users:")
        print("-" * 60)

        for row in rows:
            print(
                f"ID: {row[0]}, Username: {row[1]}, Full Name: {row[2]}, "
                f"Role: {row[3]}, Status: {row[4]}, Created: {row[5]}"
            )


    except Exception as e:
        print("Error retrieving users:", e)

    finally:
        cur.close()
        conn.close()


# GET USER BY ID (used by GUI when selecting a row)
def get_user_by_id(user_id):
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()

        sql = """
        SELECT user_id, username, full_name, role, status, created_at
        FROM users
        WHERE user_id = %s;
        """

        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        if not row:
            print("User not found.")
            return None

        return {
            "user_id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
            "status": row[4],
            "created_at": row[5]
        }

    except Exception as e:
        print("Error retrieving user:", e)
        return None

    finally:
        cur.close()
        conn.close()


# UPDATE USER (USERNAME + PASSWORD) function
# Admin updates username or password
def update_user(old_username, new_username=None, new_password=None):
    conn = get_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()

        cur.execute("SELECT username, password FROM users WHERE username = %s;", (old_username,))
        existing = cur.fetchone()

        if not existing:
            print("User not found.")
            return

        updates = []
        values = []

        if new_username:
            updates.append("username = %s")
            values.append(new_username)

        if new_password:
            updates.append("password = %s")
            values.append(new_password)

        if not updates:
            print("Nothing to update.")
            return

        sql = f"UPDATE users SET {', '.join(updates)} WHERE username = %s;"
        values.append(old_username)

        cur.execute(sql, tuple(values))
        conn.commit()

        print("User updated successfully.")

    except psycopg2.errors.UniqueViolation:
        print(f"Username '{new_username}' already exists.")
        conn.rollback()

    except Exception as e:
        print("Error updating user:", e)
        conn.rollback()

    finally:
        cur.close()
        conn.close()



# TOGGLE USER STATUS (ACTIVE / INACTIVE) function
# Deactivate or reactivate a user
def toggle_user_status(username):
    conn = get_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()

        cur.execute("SELECT status FROM users WHERE username = %s;", (username,))
        user = cur.fetchone()

        if not user:
            print("User not found.")
            return

        current_status = user[0]
        new_status = "Inactive" if current_status == "Active" else "Active"

        cur.execute("UPDATE users SET status = %s WHERE username = %s;", (new_status, username))
        conn.commit()

        print(f"User '{username}' status changed to {new_status}.")

    except Exception as e:
        print("Error updating status:", e)
        conn.rollback()

    finally:
        cur.close()
        conn.close()


 
# LOGIN USER
# Engineers and Admins must log in before using system
def login_user(username, password):
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()

        sql = """
        SELECT user_id, full_name, role, status
        FROM users
        WHERE username = %s AND password = %s;
        """

        cur.execute(sql, (username, password))
        user = cur.fetchone()

        if not user:
            print("Invalid username or password.")
            return None

        user_id, full_name, role, status = user

        if status != "Active":
            print("Account is deactivated.")
            return None

        print(f"Login successful. Welcome, {full_name}!")

        return {
            "user_id": user_id,
            "full_name": full_name,
            "role": role
        }

    except Exception as e:
        print("Login error:", e)
        return None

    finally:
        cur.close()
        conn.close()