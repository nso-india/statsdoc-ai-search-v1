import os


def get_env_variable(var_name, default=None, boolean=False):
    """Get the environment variable or return exception."""
    try:
        value = os.getenv(var_name, default)
        if boolean:
            try:
                value = int(value)
            except ValueError:
                raise ValueError(f"Environment variable {var_name} must be an integer")  # noqa
            value = bool(int(value))
        return value
    except KeyError:
        raise Exception(f"Set the {var_name} environment variable")