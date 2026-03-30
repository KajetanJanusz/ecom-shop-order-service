import multiprocessing

bind = "0.0.0.0:5001"
loglevel = "info"
max_requests = 1000
capture_output = True
reload = False
worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 300
