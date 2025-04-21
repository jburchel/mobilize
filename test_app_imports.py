#!/usr/bin/env python3
"""
Simple test script to verify app imports and dependencies.
"""
import sys
import importlib
import inspect
import pkg_resources

def check_import(module_name):
    """Attempt to import a module and report its status."""
    try:
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        return module
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return None

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
    app_success = False
    if core_success:
        print("\n--- App Modules ---")
        modules = {}
        for module_name in app_modules:
            module = check_import(module_name)
            if module:
                modules[module_name] = module
            else:
                break
        
        # Check for app.py module and create_app function
        print("\n--- App Structure ---")
        try:
            app_module = importlib.import_module("app")
            if hasattr(app_module, "create_app"):
                print("✅ Found create_app() function in app module")
                if callable(app_module.create_app):
                    print("✅ create_app is callable")
                    app_instance = app_module.create_app()
                    print(f"✅ Successfully created app instance: {app_instance}")
                    print(f"   App name: {app_instance.name}")
                    print(f"   Endpoints: {list(app_instance.url_map.iter_rules())[:5]} (showing first 5)")
                    app_success = True
                else:
                    print("❌ create_app exists but is not callable")
            else:
                print("❌ No create_app function found in app module")
                print(f"   Available attributes: {dir(app_module)[:10]} (showing first 10)")
                if hasattr(app_module, "app"):
                    print(f"✅ Found 'app' instance in app module: {app_module.app}")
                    app_success = True
                else:
                    print("❌ No 'app' instance found in app module")
        except Exception as e:
            print(f"❌ Error checking app structure: {e}")
    else:
        print("\n❌ Skipping app module checks due to core module import failures")
    
    # Final status
    print("\n=== Test Summary ===")
    if core_success and app_success and versions_success:
        print("✅ All tests passed! Application dependencies look good.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the details above.")
        sys.exit(1) 