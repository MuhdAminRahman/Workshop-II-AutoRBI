import psycopg2

# DATABASE CONNECTION CONFIGURATION 
DB_CONFIG = {
    "dbname": "rbi_database", 
    "user": "rbi_user",
    "password": "AutoRBI@2025",
    "host": "localhost",
    "port": "5432"
}

def get_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Database connection successful.")
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

# Optional: test the connection when this file runs directly
if __name__ == "__main__":
    get_connection()
