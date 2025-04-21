#!/usr/bin/env python3
"""
Simple test script to verify app imports and dependencies.
"""
import sys
import importlib
import pkg_resources

def check_import(module_name):
    """Attempt to import a module and report its status."""
    try:
        importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return False

def check_package_version(package_name):
    """Check the installed version of a package."""
    try:
        version = pkg_resources.get_distribution(package_name).version
        print(f"📦 {package_name} version: {version}")
        return True
    except pkg_resources.DistributionNotFound:
        print(f"❌ Package {package_name} not found")
        return False

if __name__ == "__main__":
    print("=== Testing Application Imports ===")
    
    # Core Flask imports
    core_modules = [
        "flask",
        "flask_migrate",
        "flask_cors",
        "flask_login",
        "flask_jwt_extended",
        "flask_wtf",
        "flask_limiter",
        "flask_talisman"
    ]
    
    # App-specific imports
    app_modules = [
        "app",
        "app.config",
        "app.extensions",
        "app.auth",
        "app.models",
        "app.routes"
    ]
    
    # Check core module imports
    print("\n--- Core Modules ---")
    core_success = all(check_import(module) for module in core_modules)
    
    # Check versions of key packages
    print("\n--- Package Versions ---")
    packages_to_check = [
        "flask",
        "flask-migrate",
        "flask-cors",
        "flask-login",
        "flask-jwt-extended",
        "flask-wtf",
        "flask-limiter",
        "flask-talisman",
        "gunicorn",
        "sqlalchemy"
    ]
    versions_success = all(check_package_version(pkg) for pkg in packages_to_check)
    
    # Only check app imports if core modules are successful
    if core_success:
        print("\n--- App Modules ---")
        app_success = all(check_import(module) for module in app_modules)
    else:
        app_success = False
        print("\n❌ Skipping app module checks due to core module import failures")
    
    # Final status
    print("\n=== Test Summary ===")
    if core_success and app_success and versions_success:
        print("✅ All tests passed! Application dependencies look good.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the details above.")
        sys.exit(1) 