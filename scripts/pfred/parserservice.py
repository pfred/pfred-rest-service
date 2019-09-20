#! /usr/bin/env python3
# Change in container code to /home/pfred/bin/python-3.6.2/bin/env python3

import argparse
import logging
from projectloghandler import ch
from exceptionlogger import ExceptionLogger


class ParserService(argparse.ArgumentParser):
    logger = ExceptionLogger.create_logger(ch, logging.INFO, __name__)

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
