"""
statuswriter
~~~~~~~~~~~~

A module for writing basic status updates to a command line interface.
"""
def split_time(duration: float) -> tuple[int, int, int]:
    """Deremine how many hours, minutes, and seconds are in a number
    of seconds.
    
    :param duration: The number of seconds.
    :return: A :class:tuple object.
    :rtype: tuple
    """
    s = duration % 60
    duration -= s
    m = duration % 3600
    duration -= m
    h = int(duration / 3600)
    m = int(m / 60)
    s = int(s)
    return h, m, s
