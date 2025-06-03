import multiprocessing
import os

# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/settings.html

# Bind to 0.0.0.0:8080
bind = "0.0.0.0:8080"

# Worker Settings
workers = 1  # Keep this at 1 for Cloud Run
threads = 4  # Reduce from 8 to 4 for better stability
worker_class = "gthread"
timeout = 120  # Add a reasonable timeout instead of 0

# Logging
loglevel = os.getenv("LOG_LEVEL", "info").lower()
accesslog = "-"  # stdout
errorlog = "-"  # stderr
capture_output = True
enable_stdio_inheritance = True

# Startup and Reload
preload_app = False  # Don't preload for better error visibility
reload = False  # Disable auto-reload in production

# Function to handle when worker starts
def on_starting(server):
    print("Gunicorn server is starting")
    # Make sure the app can be imported
    try:
        from wsgi import app
        print("Successfully imported the application")
    except Exception as e:
        print(f"ERROR: Failed to import application: {e}")
        import traceback
        traceback.print_exc()

# Function to initialize worker process
def post_fork(server, worker):
    print(f"Worker {worker.pid} spawned")

# Function when worker exits
def worker_exit(server, worker):
    print(f"Worker {worker.pid} exited")

# Function when worker fails
def worker_abort(worker):
    print(f"Worker {worker.pid} aborted")

# Print detailed application startup errors
def post_worker_init(worker):
    print(f"Worker {worker.pid} initialized")

# Function to log exceptions
def worker_int(worker):
    print(f"Worker {worker.pid} interrupted")

# Handle worker crashes
def worker_abort(worker):
    print(f"Worker {worker.pid} aborted unexpectedly") 
