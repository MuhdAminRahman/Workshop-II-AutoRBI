import psycopg2
from db_connection import get_connection


# ======================================================
# CREATE COMPONENT
# ======================================================
def create_component(equipment_id, part):
    """
    Inserts a new component into the database.
    If material_spec does NOT exist in type_material → set it to NULL.
    This avoids insertion failure and allows engineers to fill it later.
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()

        # -----------------------------
        # 1. Check material_spec validity
        # -----------------------------
        material_spec = part.get("material_spec")

        if material_spec:  # only check if it exists
            cur.execute(
                "SELECT material_spec FROM type_material WHERE material_spec = %s;",
                (material_spec,)
            )
            exists = cur.fetchone()

            if not exists:
                print(f"⚠ Warning: material_spec '{material_spec}' not found. Setting to NULL.")
                material_spec = None
        else:
            material_spec = None

        # -----------------------------
        # 2. Insert component
        # -----------------------------
        sql = """
        INSERT INTO component (
            equipment_id, part_name, phase, fluid,
            material_spec, material_grade, insulation,
            design_temp, design_pressure, operating_temp, operating_pressure
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING component_id;
        """

        cur.execute(sql, (
            equipment_id,
            part.get("part_name"),
            part.get("phase"),
            part.get("fluid"),
            material_spec,
            part.get("material_grade"),
            part.get("insulation"),
            part.get("design_temp"),
            part.get("design_pressure"),
            part.get("operating_temp"),
            part.get("operating_pressure")
        ))

        component_id = cur.fetchone()[0]
        conn.commit()

        print("Component created successfully.")
        return component_id

    except Exception as e:
        print("Error creating component:", e)
        conn.rollback()
        return None

    finally:
        cur.close()
        conn.close()



# ======================================================
# GET COMPONENTS BY EQUIPMENT
# ======================================================
def get_components_by_equipment(equipment_id):
    """
    Retrieves all components belonging to one equipment.
    Useful for displaying component list in GUI.
    """
    conn = get_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()

        sql = """
        SELECT 
            component_id, part_name, phase, fluid,
            material_spec, material_grade, insulation,
            design_temp, design_pressure, operating_temp, operating_pressure
        FROM component
        WHERE equipment_id = %s
        ORDER BY component_id;
        """

        cur.execute(sql, (equipment_id,))
        rows = cur.fetchall()

        component_list = []
        for row in rows:
            component_list.append({
                "component_id": row[0],
                "part_name": row[1],
                "phase": row[2],
                "fluid": row[3],
                "material_spec": row[4],
                "material_grade": row[5],
                "insulation": row[6],
                "design_temp": row[7],
                "design_pressure": row[8],
                "operating_temp": row[9],
                "operating_pressure": row[10]
            })

        return component_list

    except Exception as e:
        print("Error retrieving components:", e)
        return []

    finally:
        cur.close()
        conn.close()



# ======================================================
# GET COMPONENT BY ID
# ======================================================
def get_component_by_id(component_id):
    """
    Retrieve one component for editing.
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()

        sql = """
        SELECT 
            component_id, equipment_id, part_name, phase, fluid,
            material_spec, material_grade, insulation,
            design_temp, design_pressure, operating_temp, operating_pressure
        FROM component
        WHERE component_id = %s;
        """

        cur.execute(sql, (component_id,))
        row = cur.fetchone()

        if not row:
            print("Component not found.")
            return None

        return {
            "component_id": row[0],
            "equipment_id": row[1],
            "part_name": row[2],
            "phase": row[3],
            "fluid": row[4],
            "material_spec": row[5],
            "material_grade": row[6],
            "insulation": row[7],
            "design_temp": row[8],
            "design_pressure": row[9],
            "operating_temp": row[10],
            "operating_pressure": row[11],
        }

    except Exception as e:
        print("Error retrieving component:", e)
        return None

    finally:
        cur.close()
        conn.close()



# ======================================================
# UPDATE COMPONENT
# ======================================================
def update_component(component_id, **fields):
    """
    Update a component.
    If a new material_spec is provided and does NOT exist in type_material,
    it will be automatically inserted.
    """
    conn = get_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()

        # -----------------------------
        # Check for material_spec updates
        # -----------------------------
        if "material_spec" in fields:
            new_spec = fields["material_spec"]

            if new_spec is not None and new_spec != "":
                # Check if new material_spec exists
                cur.execute("""
                    SELECT material_spec 
                    FROM type_material 
                    WHERE material_spec = %s;
                """, (new_spec,))
                
                exists = cur.fetchone()

                # If not exist → insert automatically
                if not exists:
                    print(f"⚠ Material '{new_spec}' not found. Auto-inserting into type_material table.")
                    cur.execute("""
                        INSERT INTO type_material (material_spec, material_type)
                        VALUES (%s, 'Unknown');
                    """, (new_spec,))
                    conn.commit()

        # -----------------------------
        # Build dynamic update query
        # -----------------------------
        updates = []
        values = []

        for field, value in fields.items():
            updates.append(f"{field} = %s")
            values.append(value)

        if not updates:
            print("Nothing to update.")
            return

        sql = f"""
        UPDATE component
        SET {', '.join(updates)}
        WHERE component_id = %s;
        """

        values.append(component_id)

        cur.execute(sql, tuple(values))
        conn.commit()

        print("Component updated successfully.")

    except Exception as e:
        print("Error updating component:", e)
        conn.rollback()

    finally:
        cur.close()
        conn.close()


# ======================================================
# DELETE COMPONENT
# ======================================================
def delete_component(component_id):
    """
    Delete a single component.
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()

        sql = "DELETE FROM component WHERE component_id = %s;"
        cur.execute(sql, (component_id,))
        conn.commit()

        if cur.rowcount > 0:
            print("Component deleted.")
            return True
        else:
            print("Component not found.")
            return False

    except Exception as e:
        print("Error deleting component:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()
