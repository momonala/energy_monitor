import os


def print_value(value, precision=2):
    return f"{value:.{precision}f}"


def running_on_raspberry_pi():
    return os.path.isfile('/proc/device-tree/model')

