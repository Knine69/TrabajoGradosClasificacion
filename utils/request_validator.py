def validate_params(*args) -> bool:
    for arg in args:
        if not arg:
            return False
    return True


def get_request_data(request_data, *names):
    return tuple(
        request_data.get(
            name,
            'http://192.168.0.71:5000/chroma/task-status' if name == 'callback_url'
            else False)
        for name in names
    )