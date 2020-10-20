#! /usr/bin/env python3
# Change in container code to /home/pfred/bin/python-3.6.2/bin/env python3

import argparse
import logging
from exceptionlogger import ExceptionLogger
import projectloghandler as hlr


def logHandler(fname, logfile=False):
    hlr.logHandler(file=logfile, filename=fname)


class ParserService(argparse.ArgumentParser):
    def __init__(self, description):
        self.logger = ExceptionLogger.create_logger(hlr.ch, logging.INFO,
                                                    __name__)
        super().__init__(description)

    def error(self, message):
        self.logger.error(message)
        super().error(message)

    def listFromInput(self, input, element, delimiter):
        arglist = list(input.split(delimiter))
        if element in arglist:
            arglist.remove(element)
        return arglist

    def showRun(self, file, flags, input):
        msg = "Running: {}".format(file)

        for flag, inp in zip(flags, input):
            msg += " {} ".format(inp)
        self.logger.info(msg)
