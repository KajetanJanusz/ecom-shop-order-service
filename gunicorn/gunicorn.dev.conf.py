bind = "0.0.0.0:5001"
loglevel = "debug"
max_requests = 1000
capture_output = True
reload = True
worker_class = "uvicorn.workers.UvicornWorker"
workers = 1
timeout = 300
