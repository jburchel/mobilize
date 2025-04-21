import multiprocessing
import os

# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/settings.html

# Bind to 0.0.0.0:8080
bind = "0.0.0.0:8080"

# Worker Settings
workers = 1
threads = 8
worker_class = "gthread"
timeout = 0  # Disable timeout as specified in Dockerfile's CMD

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