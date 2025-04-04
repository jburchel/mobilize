import sqlite3
import os

def add_scopes_column():
    """Add scopes column to google_tokens table."""
    print("Adding scopes column to google_tokens table...")
    db_path = os.path.join(os.path.dirname(__file__), 'app.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the column already exists
    cursor.execute("PRAGMA table_info(google_tokens)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    if 'scopes' not in column_names:
        try:
            # Add the scopes column
            cursor.execute("ALTER TABLE google_tokens ADD COLUMN scopes TEXT")
            conn.commit()
            print("Successfully added scopes column to google_tokens table")
        except Exception as e:
            conn.rollback()
            print(f"Error adding scopes column: {e}")
    else:
        print("Scopes column already exists in google_tokens table")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    add_scopes_column() 