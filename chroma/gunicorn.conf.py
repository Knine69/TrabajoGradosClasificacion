bind = '0.0.0.0:5000'  # Bind to all interfaces to allow external access
workers = 2            # Number of worker processes
threads = 4            # Number of threads per worker
timeout = 120          # Timeout for requests
accesslog = '-'        # Log requests to stdout
errorlog = '-'         # Log errors to stdout
loglevel = 'debug'     # Log level (debug, info, warning, error, critical)
preload_app = False    # Do not preload the app
