import psycopg2
from db_connection import get_connection


# ======================================================
# CREATE WORK HISTORY
# ======================================================
def create_work_history(user_id, description, equipment_id=None, file_path=None):
    """
    Creates a new work history entry.
    equipment_id may be NULL (for actions before extraction).
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO work_history (user_id, equipment_id, description, file_path)
        VALUES (%s, %s, %s, %s)
        RETURNING history_id;
        """

        cur.execute(sql, (user_id, equipment_id, description, file_path))
        history_id = cur.fetchone()[0]
        conn.commit()

        print("Work history record created.")
        return history_id

    except Exception as e:
        print("Error creating work history:", e)
        conn.rollback()
        return None

    finally:
        cur.close()
        conn.close()



# ======================================================
# RETRIEVE HISTORY BY USER
# ======================================================
def get_history_by_user(user_id):
    """
    Returns all work activities performed by a specific user.
    """
    conn = get_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT history_id, user_id, equipment_id, description, file_path, timestamp
        FROM work_history
        WHERE user_id = %s
        ORDER BY timestamp DESC;
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        history_list = []
        for row in rows:
            history_list.append({
                "history_id": row[0],
                "user_id": row[1],
                "equipment_id": row[2],
                "description": row[3],
                "file_path": row[4],
                "timestamp": row[5]
            })

        return history_list

    except Exception as e:
        print("Error retrieving user history:", e)
        return []

    finally:
        cur.close()
        conn.close()



# ======================================================
# RETRIEVE HISTORY BY EQUIPMENT
# ======================================================
def get_history_by_equipment(equipment_id):
    """
    Returns all work activities related to a specific equipment.
    """
    conn = get_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT history_id, user_id, equipment_id, description, file_path, timestamp
        FROM work_history
        WHERE equipment_id = %s
        ORDER BY timestamp DESC;
        """

        cur.execute(sql, (equipment_id,))
        rows = cur.fetchall()

        history_list = []
        for row in rows:
            history_list.append({
                "history_id": row[0],
                "user_id": row[1],
                "equipment_id": row[2],
                "description": row[3],
                "file_path": row[4],
                "timestamp": row[5]
            })

        return history_list

    except Exception as e:
        print("Error retrieving equipment history:", e)
        return []

    finally:
        cur.close()
        conn.close()



# ======================================================
# RETRIEVE ALL HISTORY (Admin use)
# ======================================================
def get_all_history():
    """
    Returns all work history entries.
    Only Admin should access this.
    """
    conn = get_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT history_id, user_id, equipment_id, description, file_path, timestamp
        FROM work_history
        ORDER BY timestamp DESC;
        """

        cur.execute(sql)
        rows = cur.fetchall()

        history_list = []
        for row in rows:
            history_list.append({
                "history_id": row[0],
                "user_id": row[1],
                "equipment_id": row[2],
                "description": row[3],
                "file_path": row[4],
                "timestamp": row[5]
            })

        return history_list

    except Exception as e:
        print("Error retrieving all history:", e)
        return []

    finally:
        cur.close()
        conn.close()



# ======================================================
# DELETE HISTORY (Rarely used)
# ======================================================
def delete_history(history_id):
    """
    Deletes a single work history entry.
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()

        sql = "DELETE FROM work_history WHERE history_id = %s;"
        cur.execute(sql, (history_id,))
        conn.commit()

        if cur.rowcount > 0:
            print("History record deleted.")
            return True
        else:
            print("History not found.")
            return False

    except Exception as e:
        print("Error deleting history:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()
