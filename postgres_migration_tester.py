#!/usr/bin/env python3
"""
PostgreSQL Migration Compatibility Tester

This script tests the compatibility of all migration files with PostgreSQL by:
1. Connecting to PostgreSQL using the production connection string
2. Analyzing all migration files for SQLite-specific syntax
3. Generating SQL for the migrations without executing them
4. Identifying potential compatibility issues

Usage:
    python3 postgres_migration_tester.py [--connection-string=<conn_string>]
"""

import os
import sys
import re
import argparse
import importlib.util
from io import StringIO
from contextlib import redirect_stdout, contextmanager
from datetime import datetime
import traceback

# Try importing necessary SQLAlchemy components
try:
    from sqlalchemy import create_engine, text, inspect
    from alembic.operations import Operations
    from alembic.migration import MigrationContext
except ImportError:
    print("Required packages not found. Please install them with:")
    print("pip install sqlalchemy alembic psycopg2-binary")
    sys.exit(1)


# Constants
MIGRATIONS_DIR = os.path.join('migrations', 'versions')
SQLITE_SPECIFIC_PATTERNS = [
    r'PRAGMA',                    # SQLite PRAGMA statements
    r'AUTOINCREMENT',             # SQLite's AUTOINCREMENT (PostgreSQL uses SERIAL)
    r'IFNULL',                    # SQLite's IFNULL (PostgreSQL uses COALESCE)
    r'RANDOM\(\)',                # SQLite's RANDOM() (PostgreSQL uses random())
    r'GLOB',                      # SQLite's GLOB (PostgreSQL uses similar_to or ~)
    r'datetime\(\)',              # SQLite's datetime() (PostgreSQL's now())
    r'DATETIME\(\'now\'',         # SQLite's DATETIME('now') (PostgreSQL's now())
    r'LIMIT \d+ OFFSET \d+',      # Check for SQLite-style pagination
    r'REPLACE INTO',              # SQLite's REPLACE INTO (PostgreSQL uses INSERT ON CONFLICT)
    r'VACUUM',                    # SQLite's VACUUM (PostgreSQL uses VACUUM FULL)
    r'CAST\(.+ AS TEXT\)',        # SQLite's TEXT (PostgreSQL often uses VARCHAR)
    r'REGEXP',                    # SQLite's REGEXP (PostgreSQL uses ~ or similar)
    r'date\(datetime\(\'now\'',   # SQLite date from datetime (PostgreSQL: current_date)
    r'julianday',                 # SQLite's julianday function
    r'strftime',                  # SQLite's string format function
    r'char\(\d+\)',               # SQLite's char function
    r'length\(.+\) = 0',          # SQLite's length check (PostgreSQL often has better functions)
    r'hex\(',                     # SQLite's hex function
    r'instr\(',                   # SQLite's instr function (PostgreSQL uses position)
    r'last_insert_rowid\(\)',     # SQLite's last insert ID (PostgreSQL uses RETURNING)
]

# PostgreSQL-specific issues to check
POSTGRESQL_ISSUES = [
    r'ADD COLUMN .+ NOT NULL',    # PostgreSQL needs a default for NOT NULL columns in ADD COLUMN
    r'DROP COLUMN.*CASCADE',      # Check for cascading drops which might behave differently
    r'CREATE\s+INDEX\s+\w+\s+ON',  # Check index names for length limits
    r'CREATE\s+TABLE\s+IF NOT EXISTS',  # Check for IF NOT EXISTS usage
    r'ADD CONSTRAINT\s+\w{60,}',  # Check constraint names for length limits
    r'ALTER\s+TABLE\s+RENAME\s+TO',  # Table renames have different behavior
]


class MigrationAnalyzer:
    """Analyze migration files for PostgreSQL compatibility."""
    
    def __init__(self, db_url=None):
        """Initialize the analyzer with database URL."""
        self.db_url = db_url
        self.engine = None
        if db_url:
            try:
                self.engine = create_engine(db_url)
                # Test the connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                print(f"Successfully connected to PostgreSQL database")
            except Exception as e:
                print(f"Failed to connect to PostgreSQL: {e}")
                self.engine = None
    
    def get_migration_files(self):
        """Get all migration files in the migrations directory."""
        try:
            if not os.path.exists(MIGRATIONS_DIR):
                print(f"Migration directory {MIGRATIONS_DIR} not found.")
                return []
                
            migration_files = [f for f in os.listdir(MIGRATIONS_DIR) 
                             if f.endswith('.py') and not f.startswith('__')]
            return sorted(migration_files)
        except Exception as e:
            print(f"Error reading migration files: {e}")
            return []
    
    def analyze_migration_file(self, filename):
        """Analyze a single migration file for PostgreSQL compatibility."""
        filepath = os.path.join(MIGRATIONS_DIR, filename)
        
        # Read the file content
        try:
            with open(filepath, 'r') as f:
                content = f.read()
        except Exception as e:
            return {
                'filename': filename,
                'status': 'error',
                'message': f"Could not read file: {e}",
                'issues': []
            }
        
        # Check for SQLite-specific patterns
        issues = []
        for pattern in SQLITE_SPECIFIC_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for match in matches:
                    issues.append({
                        'type': 'sqlite_specific',
                        'pattern': pattern,
                        'match': match,
                        'severity': 'high'
                    })
        
        # Check for potential PostgreSQL issues
        for pattern in POSTGRESQL_ISSUES:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for match in matches:
                    issues.append({
                        'type': 'postgresql_issue',
                        'pattern': pattern,
                        'match': match,
                        'severity': 'medium'
                    })
        
        # Extract SQL commands
        sql_commands = self.extract_sql_commands(content)
        
        # Check for direct SQL uses
        direct_sql_count = len(re.findall(r'text\(["\']', content, re.IGNORECASE))
        direct_sql_count += len(re.findall(r'execute\(["\']', content, re.IGNORECASE))
        
        # Check alembic operations
        alembic_ops = {
            'add_column': len(re.findall(r'add_column\(', content)),
            'drop_column': len(re.findall(r'drop_column\(', content)),
            'create_table': len(re.findall(r'create_table\(', content)),
            'drop_table': len(re.findall(r'drop_table\(', content)),
            'create_index': len(re.findall(r'create_index\(', content)),
            'drop_index': len(re.findall(r'drop_index\(', content)),
            'create_foreign_key': len(re.findall(r'create_foreign_key\(', content)),
            'drop_constraint': len(re.findall(r'drop_constraint\(', content)),
        }
        
        # Try to import and analyze the migration module
        module_analysis = self.analyze_migration_module(filename, filepath)
        
        return {
            'filename': filename,
            'status': 'analyzed',
            'issues': issues,
            'sql_commands': sql_commands,
            'direct_sql_count': direct_sql_count,
            'alembic_operations': alembic_ops,
            'module_analysis': module_analysis
        }
    
    def extract_sql_commands(self, content):
        """Extract SQL commands from the migration file."""
        sql_pattern = r'text\(["\'](.+?)["\'][\),]|execute\(["\'](.+?)["\'][\),]|op\.execute\(["\'](.+?)["\'][\),]'
        matches = re.findall(sql_pattern, content)
        
        sql_commands = []
        for match in matches:
            command = next((cmd for cmd in match if cmd), None)
            if command:
                sql_commands.append(command)
        
        return sql_commands
    
    def analyze_migration_module(self, filename, filepath):
        """Try to import and analyze the migration module."""
        try:
            # Extract the module name
            module_name = filename[:-3]  # Remove .py extension
            
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the upgrade and downgrade functions
            has_upgrade = hasattr(module, 'upgrade')
            has_downgrade = hasattr(module, 'downgrade')
            
            # Check revision info
            revision = getattr(module, 'revision', None)
            down_revision = getattr(module, 'down_revision', None)
            
            return {
                'has_upgrade': has_upgrade,
                'has_downgrade': has_downgrade,
                'revision': revision,
                'down_revision': down_revision,
                'error': None
            }
        except Exception as e:
            return {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def test_migration_sql(self, filename):
        """Test generating SQL for a migration without executing it."""
        if not self.engine:
            return {
                'status': 'error',
                'message': 'No database connection available'
            }
        
        filepath = os.path.join(MIGRATIONS_DIR, filename)
        module_name = filename[:-3]  # Remove .py extension
        
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if not hasattr(module, 'upgrade'):
                return {
                    'status': 'error',
                    'message': 'No upgrade function found in migration'
                }
            
            # Capture stdout to get the SQL commands
            sql_output = StringIO()
            with redirect_stdout(sql_output):
                # Create a connection and context
                with self.engine.connect() as conn:
                    ctx = MigrationContext.configure(
                        conn,
                        opts={
                            'as_sql': True,  # Generate SQL instead of executing
                            'target_metadata': None
                        }
                    )
                    
                    # Create operation object
                    op = Operations(ctx)
                    
                    # Execute the upgrade function with op
                    try:
                        # Check if upgrade accepts the op parameter
                        import inspect
                        sig = inspect.signature(module.upgrade)
                        if len(sig.parameters) > 0:
                            module.upgrade(op)
                        else:
                            # Set global op variable
                            module.__dict__['op'] = op
                            module.upgrade()
                            
                        return {
                            'status': 'success',
                            'sql_output': sql_output.getvalue(),
                            'message': 'Successfully generated SQL'
                        }
                    except Exception as e:
                        return {
                            'status': 'error',
                            'message': f'Error generating SQL: {e}',
                            'traceback': traceback.format_exc()
                        }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error importing migration module: {e}',
                'traceback': traceback.format_exc()
            }
    
    def run_full_analysis(self):
        """Run a full analysis of all migration files."""
        migration_files = self.get_migration_files()
        if not migration_files:
            print("No migration files found to analyze.")
            return []
        
        print(f"Found {len(migration_files)} migration files to analyze.")
        results = []
        
        for filename in migration_files:
            print(f"Analyzing {filename}...")
            result = self.analyze_migration_file(filename)
            results.append(result)
            
            # Report issues
            if result['issues']:
                print(f"  Found {len(result['issues'])} potential issues:")
                for issue in result['issues']:
                    print(f"  - {issue['type']}: {issue['match']} (severity: {issue['severity']})")
            else:
                print("  No issues found.")
        
        return results
    
    def generate_report(self, results):
        """Generate a detailed report of the migration analysis."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = f"""
# PostgreSQL Migration Compatibility Report
Generated: {now}

## Summary
- Total migration files analyzed: {len(results)}
- Files with issues: {sum(1 for r in results if r.get('issues'))}
- Total potential issues found: {sum(len(r.get('issues', [])) for r in results)}

## Detailed Analysis

"""
        for result in results:
            report += f"### {result['filename']}\n"
            
            if result['status'] == 'error':
                report += f"**Status**: Error - {result.get('message', 'Unknown error')}\n\n"
                continue
            
            # Module analysis
            module_analysis = result.get('module_analysis', {})
            if module_analysis:
                if 'error' in module_analysis and module_analysis['error']:
                    report += f"**Module Error**: {module_analysis['error']}\n\n"
                else:
                    report += f"**Revision**: {module_analysis.get('revision', 'Not found')}\n"
                    report += f"**Down Revision**: {module_analysis.get('down_revision', 'Not found')}\n"
                    report += f"**Has Upgrade**: {module_analysis.get('has_upgrade', False)}\n"
                    report += f"**Has Downgrade**: {module_analysis.get('has_downgrade', False)}\n\n"
            
            # Alembic operations
            ops = result.get('alembic_operations', {})
            if ops:
                report += "**Alembic Operations**:\n"
                for op_name, count in ops.items():
                    if count > 0:
                        report += f"- {op_name}: {count}\n"
                report += "\n"
            
            # SQL Commands
            sql_commands = result.get('sql_commands', [])
            if sql_commands:
                report += f"**Direct SQL Commands** ({len(sql_commands)}):\n"
                for i, cmd in enumerate(sql_commands, 1):
                    report += f"{i}. `{cmd}`\n"
                report += "\n"
            
            # Issues
            issues = result.get('issues', [])
            if issues:
                report += f"**Potential Issues** ({len(issues)}):\n"
                for issue in issues:
                    report += f"- [{issue['severity']}] {issue['type']}: `{issue['match']}`\n"
                report += "\n"
            else:
                report += "**No issues detected**\n\n"
                
            report += "---\n\n"
        
        return report

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='PostgreSQL Migration Compatibility Tester')
    parser.add_argument('--connection-string', dest='conn_string', 
                      default=os.environ.get('DATABASE_URL', "postgresql://postgres.fwnitauuyzxnsvgsbrzr:RV4QOygx0LpqOjzx@aws-0-us-east-1.pooler.supabase.com:5432/postgres"),
                      help='PostgreSQL connection string')
    parser.add_argument('--output', dest='output_file',
                      default='migration_compatibility_report.md',
                      help='Output file for the report')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    print("PostgreSQL Migration Compatibility Tester")
    print("=========================================")
    print(f"Using database URL: {args.conn_string}")
    
    analyzer = MigrationAnalyzer(args.conn_string)
    results = analyzer.run_full_analysis()
    
    if results:
        # Generate the report
        report = analyzer.generate_report(results)
        
        # Write to file
        with open(args.output_file, 'w') as f:
            f.write(report)
        
        print(f"\nReport written to {args.output_file}")
    else:
        print("No results to report.") 