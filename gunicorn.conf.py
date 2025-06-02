# Gunicorn configuration file
import os
import multiprocessing

# Server socket
bind = "0.0.0.0:" + os.environ.get("PORT", "8080")

# Worker processes
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "gthread"
threads = int(os.environ.get("GUNICORN_THREADS", "4"))

# Timeout
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))

# Server mechanics
daemon = False
rawenv = ["DJANGO_SETTINGS_MODULE=config.settings"]
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
logfile = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")
accesslog = "-"
access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
errorlog = "-"

# Process naming
proc_name = None

# Server hooks
def on_starting(server):
    server.log.info("Starting Gunicorn server with configuration:")
    server.log.info(f"Bind: {bind}")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Worker class: {worker_class}")
    server.log.info(f"Threads: {threads}")
    server.log.info(f"Timeout: {timeout}")

def on_exit(server):
    server.log.info("Shutting down Gunicorn server")

# Specify the WSGI application
wsgi_app = "wsgi:application"
