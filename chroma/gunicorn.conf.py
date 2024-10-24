bind = '127.0.0.1:5000'  # Address and port to bind to
workers = 2            # Number of worker processes
threads = 4            # Number of threads per worker
timeout = 120          # Timeout for requests
accesslog = '-'        # Log requests to stdout
errorlog = '-'         # Log errors to stdout
loglevel = 'debug'      # Log level (can be debug, info, warning, error,
# critical)
preload_app = False
