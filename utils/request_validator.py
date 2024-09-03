def validate_params(*args) -> bool:
    for arg in args:
        if not arg:
            return False
    return True
