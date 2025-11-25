import psycopg2
from db_connection import get_connection


# ======================================================
# CREATE EQUIPMENT
# ======================================================
def create_equipment(equipment_no, pmt_no, description, drawing_file_path, user_id):
    """
    Inserts a new equipment record into the database.
    equipment_no must be unique.
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO equipment (equipment_no, pmt_no, description, drawing_file_path, user_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING equipment_id;
        """

        cur.execute(sql, (equipment_no, pmt_no, description, drawing_file_path, user_id))
        equipment_id = cur.fetchone()[0]
        conn.commit()

        print("Equipment created successfully.")
        return equipment_id

    except psycopg2.errors.UniqueViolation:
        print(f"Equipment number '{equipment_no}' already exists.")
        conn.rollback()
        return None

    except Exception as e:
        print("Error creating equipment:", e)
        conn.rollback()
        return None

    finally:
        cur.close()
        conn.close()



# ======================================================
# RETRIEVE ALL EQUIPMENT
# ======================================================
def get_all_equipment():
    """
    Retrieves all equipment records.
    Used by GUI to fill equipment table.
    """
    conn = get_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT equipment_id, equipment_no, pmt_no, description, drawing_file_path, user_id
        FROM equipment
        ORDER BY equipment_id;
        """

        cur.execute(sql)
        rows = cur.fetchall()

        equipment_list = []
        for row in rows:
            equipment_list.append({
                "equipment_id": row[0],
                "equipment_no": row[1],
                "pmt_no": row[2],
                "description": row[3],
                "drawing_file_path": row[4],
                "user_id": row[5]
            })

        return equipment_list

    except Exception as e:
        print("Error retrieving equipment:", e)
        return []

    finally:
        cur.close()
        conn.close()



# ======================================================
# RETRIEVE EQUIPMENT BY ID
# ======================================================
def get_equipment_by_id(equipment_id):
    """
    Retrieves a single equipment record by its ID.
    Used when GUI selects a row from table.
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()

        sql = """
        SELECT equipment_id, equipment_no, pmt_no, description, drawing_file_path, user_id
        FROM equipment
        WHERE equipment_id = %s;
        """

        cur.execute(sql, (equipment_id,))
        row = cur.fetchone()

        if not row:
            print("Equipment not found.")
            return None

        return {
            "equipment_id": row[0],
            "equipment_no": row[1],
            "pmt_no": row[2],
            "description": row[3],
            "drawing_file_path": row[4],
            "user_id": row[5]
        }

    except Exception as e:
        print("Error retrieving equipment:", e)
        return None

    finally:
        cur.close()
        conn.close()



# ======================================================
# UPDATE EQUIPMENT
# ======================================================
def update_equipment(equipment_id, equipment_no=None, pmt_no=None, description=None, drawing_file_path=None):
    """
    Updates only provided fields.
    GUI sends equipment_id (hidden), not equipment_no.
    """
    conn = get_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()

        # Get existing data
        cur.execute("SELECT * FROM equipment WHERE equipment_id = %s;", (equipment_id,))
        existing = cur.fetchone()

        if not existing:
            print("Equipment not found.")
            return

        updated_equipment_no = equipment_no if equipment_no else existing[1]
        updated_pmt_no = pmt_no if pmt_no else existing[2]
        updated_description = description if description else existing[3]
        updated_file_path = drawing_file_path if drawing_file_path else existing[4]

        sql = """
        UPDATE equipment
        SET equipment_no = %s,
            pmt_no = %s,
            description = %s,
            drawing_file_path = %s
        WHERE equipment_id = %s;
        """

        cur.execute(sql, (
            updated_equipment_no,
            updated_pmt_no,
            updated_description,
            updated_file_path,
            equipment_id
        ))

        conn.commit()
        print("Equipment updated successfully.")

    except psycopg2.errors.UniqueViolation:
        print(f"Equipment number '{equipment_no}' already exists.")
        conn.rollback()

    except Exception as e:
        print("Error updating equipment:", e)
        conn.rollback()

    finally:
        cur.close()
        conn.close()



# ======================================================
# DELETE EQUIPMENT
# ======================================================
def delete_equipment(equipment_id):
    """
    Completely deletes equipment.
    CASCADE deletes components, work history, etc.
    """
    conn = get_connection()
    if not conn:
        return 

    try:
        cur = conn.cursor()

        sql = "DELETE FROM equipment WHERE equipment_id = %s;"
        cur.execute(sql, (equipment_id,))
        conn.commit()

        if cur.rowcount > 0:
            print("Equipment deleted successfully.")
            return True
        else:
            print("Equipment not found.")
            return False

    except Exception as e:
        print("Error deleting equipment:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()
