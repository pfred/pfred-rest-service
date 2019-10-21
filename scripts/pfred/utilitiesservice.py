import os
import re
import csv
import subprocess
import logging
import projectloghandler as hlr
from itertools import chain
from exceptionlogger import ExceptionLogger


def logHandler(fname='LogFile-pfred', logfile=False):
    global logger
    hlr.logHandler(file=logfile, filename=fname)
    logger = ExceptionLogger.create_logger(hlr.ch,
                                           logging.INFO, __name__)


def pid():
    return os.getpid()


@ExceptionLogger(None, ValueError, hlr.ch, "")
def osset(args):
    os.system('set ' + args)


@ExceptionLogger(None, ValueError, hlr.ch, "")
def rm(args):
    os.system('rm -f ' + args)


def which(prog):
    """
    Calls the UNIX command "which"
    """

    rc = subprocess.run(['which', prog])

    if not(rc.returncode):
        logger.info('{} exists in path!'.format(prog))
    else:
        logger.error('{} missing in path!'.format(prog))
        raise ValueError


@ExceptionLogger(None, KeyError, hlr.ch, "")
def env(vars):
    """
    Returns path to environment variables
    """

    if isinstance(vars, str):
        return os.environ[vars]
    return [os.environ[var] for var in vars]


@ExceptionLogger(None, ValueError, hlr.ch, "")
def run(prog, params, fname=''):
    """
    Execute binary with given arguments
    """

    args = [prog] + params

    if fname:
        dump = open(fname, 'w')
        rc = subprocess.run(args, stdout=dump)
        dump.close()
    else:
        print(args)
        rc = subprocess.run(args)

    if (rc.returncode):
        logger.error('Can\'t run {} properly!'.format(prog))
        raise ValueError


@ExceptionLogger(None, ValueError, hlr.ch, "")
def replaceMultiple(string, substitutions):
    """
    Replace a set of multiple sub strings with a new string in main string
    using regex
    """

    substrings = sorted(substitutions, key=len, reverse=True)
    regex = re.compile('|'.join(map(re.escape, substrings)))
    return regex.sub(lambda match: substitutions[match.group(0)], string)


@ExceptionLogger(None, ValueError, hlr.ch, "")
def createOutCsv(title, data, fname):
    """
    Creates output file given filename, data and title in csv format.
    Input data must be list of lists!
    """

    msg = [",".join(title)]

    for row in data:
        msg.append(",".join(map(str, row)))

    msg = '\n'.join(msg)
    outhandler = open(fname, 'w')
    outhandler.write(msg)
    outhandler.close()


@ExceptionLogger(None, ValueError, hlr.ch, "")
def readAnnotationCsv(fname):
    file = open(fname)
    reader = csv.reader(file, delimiter=',')
    return [file, reader]


def flattenList(seqslist):
    return list((chain.from_iterable(seqslist)))


@ExceptionLogger(None, ValueError, hlr.ch, "")
def flattenDic(seqsdic):
    return sorted(set(chain(*seqsdic.values())))


@ExceptionLogger(None, ValueError, hlr.ch, "")
def noDuplicates(iterable):
    return list(dict.fromkeys(iterable))
