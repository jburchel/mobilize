#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

"""
This script analyzes migration files to extract SQL commands and check for PostgreSQL compatibility.
It looks for potential SQLite-specific syntax or functions that might cause issues in PostgreSQL.
"""

MIGRATIONS_DIR = Path("migrations/versions")
SQLITE_SPECIFIC_PATTERNS = [
    r"PRAGMA",
    r"AUTOINCREMENT",
    r"ILIKE",  # PostgreSQL has this but SQLite doesn't by default
    r"sqlite_sequence",
    r"WITHOUT\s+ROWID",
    r"VACUUM",
    r"CAST\s*\(\s*.+\s+AS\s+TEXT\s*\)",  # SQLite's flexible casting
    r"datetime\s*\(\s*['\"]\w+['\"]"  # SQLite's datetime function used in specific ways
]

def analyze_migration_file(file_path):
    """Analyze a migration file for SQL commands and compatibility issues."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract SQL commands (look for op.execute or similar commands)
    sql_commands = re.findall(r"op\.execute\([\"'](.*?)[\"']\)", content, re.DOTALL)
    create_table_commands = re.findall(r"op\.create_table\([\"'](.+?)[\"'],.+?\)", content, re.DOTALL)
    add_column_commands = re.findall(r"op\.add_column\([\"'](.+?)[\"'],.*?\)", content, re.DOTALL)
    
    # Check for SQLite-specific patterns
    issues = []
    for pattern in SQLITE_SPECIFIC_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            issues.append(f"Found potentially problematic pattern: {pattern} - {len(matches)} occurrences")
    
    # Check for implicit column combinations (SQLite allows this, PostgreSQL doesn't)
    implicit_cols = re.findall(r"sa\.Column\([^,]+\)", content)
    for col in implicit_cols:
        if "nullable" not in col and "primary_key" not in col:
            issues.append(f"Column definition without explicit nullable setting: {col.strip()}")
    
    return {
        "file": file_path.name,
        "sql_commands": sql_commands,
        "create_table_commands": create_table_commands,
        "add_column_commands": add_column_commands,
        "issues": issues
    }

def main():
    if not MIGRATIONS_DIR.exists():
        print(f"Error: Migrations directory not found at {MIGRATIONS_DIR}")
        sys.exit(1)
    
    migration_files = list(MIGRATIONS_DIR.glob("*.py"))
    if not migration_files:
        print("No migration files found.")
        sys.exit(1)
    
    print(f"Found {len(migration_files)} migration files.")
    
    all_issues = []
    for file in migration_files:
        try:
            result = analyze_migration_file(file)
            print(f"\n=== {file.name} ===")
            
            if result["sql_commands"]:
                print(f"SQL Commands: {len(result['sql_commands'])}")
                for i, cmd in enumerate(result["sql_commands"]):
                    print(f"  {i+1}. {cmd[:80]}{'...' if len(cmd) > 80 else ''}")
            
            if result["create_table_commands"]:
                print(f"Create Table Commands: {len(result['create_table_commands'])}")
                for table in result["create_table_commands"]:
                    print(f"  - {table}")
            
            if result["issues"]:
                print("Issues Found:")
                for issue in result["issues"]:
                    print(f"  - {issue}")
                all_issues.extend([f"{file.name}: {issue}" for issue in result["issues"]])
        except Exception as e:
            print(f"Error analyzing {file.name}: {str(e)}")
    
    print("\n=== Summary ===")
    if all_issues:
        print(f"Found {len(all_issues)} potential issues across all migration files:")
        for i, issue in enumerate(all_issues):
            print(f"{i+1}. {issue}")
        print("\nRecommendation: Review these issues and make necessary adjustments for PostgreSQL compatibility.")
        return 1
    else:
        print("No PostgreSQL compatibility issues found in migration files.")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 