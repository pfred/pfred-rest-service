import os
import logging


def logHandler(file=False, filename='LogFile-pfred'):
    global ch
    if file:
        if os.path.exists(filename):
            os.remove(filename)
        ch = logging.FileHandler(filename)
    else:
        ch = logging.StreamHandler()


logHandler()
