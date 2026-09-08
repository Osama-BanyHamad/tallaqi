import multiprocessing

bind = "0.0.0.0:8000"
workers = max(2, multiprocessing.cpu_count())
timeout = 60
accesslog = "-"
