import requests
from flask import request, jsonify
from functools import wraps

def execute_remotely_if_needed(func):
    """Decorator that checks if remote execution is needed based on langsecure_server."""
    @wraps(func)
    def wrapper(instance, *args, **kwargs):
        server_url = instance.langsecure_server
        if server_url is not None:
            # Remote execution - make HTTP request to the remote server
            data = {"args": args, "kwargs": kwargs}
            response = requests.post(f"{server_url}/{func.__name__}", json=data)

            if response.status_code == 200:
                return response.json()  # Return the result from the remote server
            else:
                raise Exception(f"Remote invocation failed with status: {response.status_code}")
        else:
            # Local execution
            print(f"Executing {func.__name__} locally with args: {args}, kwargs: {kwargs}")
            return func(instance, *args, **kwargs)

    return wrapper


def apiroute(app, func, instance=None):
    @wraps(func)
    def wrapped(*args, **kwargs):
        # Unpack request data
        data = request.get_json()
        args = data.get('args', [])
        kwargs = data.get('kwargs', {})
        if instance != None:
            # Call the original function and return the result wrapped in jsonify
            result = func(instance, *args, **kwargs)
        else:
            result = func(*args, **kwargs)
        return jsonify(result)  # Convert the result to JSON response

    # Register the wrapped function as a Flask route
    app.add_url_rule(f'/{func.__name__}', view_func=wrapped, methods=['POST'])
