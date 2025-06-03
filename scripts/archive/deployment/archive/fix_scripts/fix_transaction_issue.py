#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_transaction_issue():
    """Fix database transaction issues by resetting any aborted transactions."""
    # Get the database connection string from environment variable
    db_connection_string = os.getenv('DB_CONNECTION_STRING')
    
    if not db_connection_string:
        print("Error: DB_CONNECTION_STRING environment variable not set")
        sys.exit(1)
    
    print("Connecting to database...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(db_connection_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check for active transactions
        cursor.execute("""
            SELECT pid, state, query_start, now() - query_start AS duration, query 
            FROM pg_stat_activity 
            WHERE state = 'active' AND pid <> pg_backend_pid();
        """)
        active_transactions = cursor.fetchall()
        
        if active_transactions:
            print(f"Found {len(active_transactions)} active transactions:")
            for tx in active_transactions:
                print(f"PID: {tx[0]}, State: {tx[1]}, Duration: {tx[3]}, Query: {tx[4][:100]}...")
        else:
            print("No active transactions found.")
        
        # Check for idle in transaction
        cursor.execute("""
            SELECT pid, state, query_start, now() - query_start AS duration, query 
            FROM pg_stat_activity 
            WHERE state = 'idle in transaction' AND pid <> pg_backend_pid();
        """)
        idle_transactions = cursor.fetchall()
        
        if idle_transactions:
            print(f"\nFound {len(idle_transactions)} idle transactions:")
            for tx in idle_transactions:
                print(f"PID: {tx[0]}, State: {tx[1]}, Duration: {tx[3]}, Query: {tx[4][:100]}...")
                
                # Terminate idle transactions that have been running for more than 1 minute
                if tx[3].total_seconds() > 60:
                    print(f"Terminating idle transaction with PID {tx[0]}")
                    cursor.execute(f"SELECT pg_terminate_backend({tx[0]});")
        else:
            print("No idle transactions found.")
        
        # Reset all connections to ensure clean state
        print("\nResetting all database connections...")
        cursor.execute("""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = current_database() 
            AND pid <> pg_backend_pid() 
            AND state = 'idle in transaction';
        """)
        
        # Vacuum the database to clean up any dead tuples
        print("\nVacuuming database to clean up...")
        cursor.execute("VACUUM;")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        print("\nDatabase connection closed")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_transaction_issue()
    if success:
        print("\nTransaction issues fixed successfully")
    else:
        print("\nFailed to fix transaction issues")
        sys.exit(1)
