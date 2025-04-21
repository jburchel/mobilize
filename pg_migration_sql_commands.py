"""
PostgreSQL Migration SQL Commands Extractor

This script extracts SQL commands from the latest migration file for PostgreSQL compatibility testing.
It directly parses the migration file and prints the SQL commands that would be executed.
"""

import os
import re
import sys
import importlib.util
from io import StringIO
from contextlib import redirect_stdout

def find_latest_migration():
    """Find the latest migration file in the migrations/versions directory."""
    migrations_dir = os.path.join('migrations', 'versions')
    try:
        migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
        if not migration_files:
            print("No migration files found in migrations/versions directory.")
            return None
            
        # Sort the files to get the latest one
        latest_migration_file = sorted(migration_files)[-1]
        print(f"Using latest migration file: {latest_migration_file}")
        
        return os.path.join(migrations_dir, latest_migration_file)
    except Exception as e:
        print(f"Error finding migration files: {e}")
        return None

def read_file_content(file_path):
    """Read the content of a file."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def extract_sql_commands(file_content):
    """Extract SQL commands from file content using regex."""
    # Pattern to match SQL in text() or text("...") or execute("...")
    sql_pattern = r'text\(["\'](.+?)["\'][\),]|execute\(["\'](.+?)["\'][\),]|op\.execute\(["\'](.+?)["\'][\),]'
    matches = re.findall(sql_pattern, file_content)
    
    sql_commands = []
    for match in matches:
        # Each match is a tuple with multiple groups, take the non-empty one
        command = next((cmd for cmd in match if cmd), None)
        if command:
            sql_commands.append(command)
    
    return sql_commands

def extract_ddl_commands(file_content):
    """Extract table creation and alteration commands."""
    # Pattern for column additions
    add_column_pattern = r'add_column\(["\'](.+?)["\'],\s*["\'](.+?)["\'],\s*(.+?),.*?\)'
    matches = re.findall(add_column_pattern, file_content)
    
    ddl_commands = []
    for match in matches:
        table, column, column_type = match
        ddl_commands.append(f"ALTER TABLE {table} ADD COLUMN {column} {column_type};")
    
    # Pattern for column drops
    drop_column_pattern = r'drop_column\(["\'](.+?)["\'],\s*["\'](.+?)["\']'
    matches = re.findall(drop_column_pattern, file_content)
    
    for match in matches:
        table, column = match
        ddl_commands.append(f"ALTER TABLE {table} DROP COLUMN {column};")
    
    # Pattern for table creation
    create_table_pattern = r'create_table\(["\'](.+?)["\']'
    matches = re.findall(create_table_pattern, file_content)
    
    for match in matches:
        table = match
        # Just indicate that a table creation command was found - can't extract the full details
        ddl_commands.append(f"-- Table creation command for table: {table}")
    
    return ddl_commands

def analyze_migration_file():
    """Analyze migration file to extract SQL commands."""
    file_path = find_latest_migration()
    if not file_path:
        return
    
    file_content = read_file_content(file_path)
    if not file_content:
        return
    
    # Extract SQL commands
    sql_commands = extract_sql_commands(file_content)
    
    # Extract DDL commands
    ddl_commands = extract_ddl_commands(file_content)
    
    # Print results
    print("\n--- DIRECT SQL COMMANDS ---")
    if sql_commands:
        for i, cmd in enumerate(sql_commands, 1):
            print(f"{i}. {cmd}")
    else:
        print("No direct SQL commands found.")
    
    print("\n--- DDL COMMANDS (EXTRACTED) ---")
    if ddl_commands:
        for i, cmd in enumerate(ddl_commands, 1):
            print(f"{i}. {cmd}")
    else:
        print("No DDL commands found.")
    
    # Try to analyze the upgrade function more comprehensively
    try:
        # Import the migration module
        module_name = os.path.basename(file_path)[:-3]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        
        # Create a StringIO to capture printed output
        captured_output = StringIO()
        
        # Replace the upgrade function with a version that prints operations
        original_upgrade = None
        
        if hasattr(module, 'upgrade'):
            original_upgrade = module.upgrade
            
            def instrumented_upgrade(*args, **kwargs):
                print("=== UPGRADE FUNCTION OPERATIONS ===")
                # Call the original upgrade function
                result = original_upgrade(*args, **kwargs)
                return result
            
            module.upgrade = instrumented_upgrade
        
        # Execute the module to load the functions
        with redirect_stdout(captured_output):
            spec.loader.exec_module(module)
            print("\n=== MIGRATION MODULE CONTENTS ===")
            print(f"Module functions: {[f for f in dir(module) if not f.startswith('_') and callable(getattr(module, f))]}")
            
            # If we find the "upgrade" function, print its code
            if hasattr(module, 'upgrade'):
                print("\n=== UPGRADE FUNCTION SOURCE ===")
                import inspect
                print(inspect.getsource(original_upgrade))
        
        print(captured_output.getvalue())
        
    except Exception as e:
        print(f"Error analyzing migration module: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== PostgreSQL Migration SQL Commands Extractor ===\n")
    analyze_migration_file()
    print("\nAnalysis complete.") 