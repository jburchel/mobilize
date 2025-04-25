#!/usr/bin/env python
"""
Test script to verify imports within the container
"""

import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print("Testing imports...")

try:
    import flask
    print("✅ flask imported successfully")
except ImportError as e:
    print(f"❌ flask import error: {e}")

try:
    import sqlalchemy
    print("✅ sqlalchemy imported successfully")
except ImportError as e:
    print(f"❌ sqlalchemy import error: {e}")

try:
    import psycopg2
    print("✅ psycopg2 imported successfully")
except ImportError as e:
    print(f"❌ psycopg2 import error: {e}")

try:
    import google.cloud.secretmanager
    print("✅ google.cloud.secretmanager imported successfully")
except ImportError as e:
    print(f"❌ google.cloud.secretmanager import error: {e}")

try:
    from app import create_app
    print("✅ app.create_app imported successfully")
except ImportError as e:
    print(f"❌ app.create_app import error: {e}")

print("Import test completed") 