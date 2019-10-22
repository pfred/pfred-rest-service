#! /usr/bin/env python3

import logging
import traceback


class ExceptionLogger:
    def __init__(self, *args, **kwargs):
        self.logr = args[0]
        self.exceptions = args[1]
        self.ch = args[2]
        self.msg = args[3]
        self.conf_kw = kwargs

    def __call__(self, func):
        def wrapper(*args, **kwargs):

            # If argument is a string, it has to provide name of logger attr

            if(args and isinstance(self.logr, str)):
                self.logr = getattr(args[0], self.logr)
                self.msg = getattr(args[0], self.msg)
            elif(self.logr is None):
                self.logr = logging.getLogger(func.__name__)
                self.logr.setLevel(logging.INFO)
                self.logr.addHandler(self.ch)
            elif not isinstance(self.logr, logging.Logger):
                print("No logger attribute given")
                raise ValueError

            # From now on logger is well defined, all exceptions are critical

            try:
                return func(*args, **kwargs)
            except self.exceptions as e:
                fmt = '%(name)s - %(levelname)s -%(message)s'
                formatter = logging.Formatter(fmt)
                self.ch.setFormatter(formatter)

                # log the exception

                exc_tb = traceback.extract_tb(e.__traceback__)
                exc_tb = exc_tb[1]
                err = [(" line {} -".format(exc_tb.lineno))]
                err.append("There was an exception '{}' in "
                           .format(self.exceptions.__name__))
                err = ' '.join(err)
                errex = [func.__name__]
                errex.append(str(e))
                errex.append(self.msg)
                err += '\n'.join(errex)
                self.logr.exception(err)
                raise
        return wrapper

    @staticmethod
    def create_logger(handler, level, name):
        """
        Creates a logging object and returns it, chance to write to a file
        """

        logger = logging.getLogger(name)
        logger.setLevel(level)
        fmt = '%(name)s - %(levelname)s - line %(lineno)d - %(message)s'
        formatter = logging.Formatter(fmt)

        # Format handler

        handler.setFormatter(formatter)

        # Add handler to logger object

        logger.addHandler(handler)

        return logger
