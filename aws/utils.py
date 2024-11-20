import re
from functools import wraps
from datetime import datetime, timedelta
from flask import request, jsonify
from collections import defaultdict

def validate_password(password):
    """
    Validate password strength.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    
    Args:
        password (str): Password to validate
        
    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
        
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
        
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
        
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
        
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
        
    return True, "Password is valid"

# Store request counts for rate limiting
request_counts = defaultdict(list)

def rate_limit(max_requests=5, window_seconds=60):
    """
    Rate limiting decorator.
    
    Args:
        max_requests (int): Maximum number of requests allowed in the time window
        window_seconds (int): Time window in seconds
        
    Returns:
        decorator: Function that implements rate limiting
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            now = datetime.now()
            ip = request.remote_addr
            
            # Remove old requests outside the window
            request_counts[ip] = [
                req_time for req_time in request_counts[ip]
                if now - req_time < timedelta(seconds=window_seconds)
            ]
            
            # Check if too many requests
            if len(request_counts[ip]) >= max_requests:
                return jsonify({
                    'error': 'Too many requests',
                    'message': f'Please wait {window_seconds} seconds before trying again'
                }), 429
                
            # Add current request
            request_counts[ip].append(now)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator
