from functools import wraps
from src.utils.colors import Colors

def log_step(step_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            Colors.print(step_name, Colors.SYSTEM)
            result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator 