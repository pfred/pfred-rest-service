#! /usr/bin/env python3

import os
import re
import csv
import subprocess
import logging
import urllib.request
import projectloghandler as hlr
from tqdm import tqdm
from urllib.error import URLError
from multiprocessing.pool import ThreadPool
from itertools import chain
from exceptionlogger import ExceptionLogger


def logHandler(fname='LogFile-pfred', logfile=False):
    global logger
    hlr.logHandler(file=logfile, filename=fname)
    logger = ExceptionLogger.create_logger(hlr.ch,
                                           logging.INFO, __name__)


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


@ExceptionLogger(None, URLError, hlr.ch, "")
def download_url(url, output_path):
    with DownloadProgressBar(unit='B', unit_scale=True,
                             miniters=1, desc=url.split('/')[-1]) as t:
        urllib.request.urlretrieve(url, filename=output_path,
                                   reporthook=t.update_to)


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


@ExceptionLogger(None, URLError, hlr.ch, "")
def FetchEntry(entry):
    path, uri, fun, ntries = entry
    if not os.path.exists(path):
        try:
            download_url(uri, path)
        except (urllib.error.ContentTooShortError) as e:
            logger.info('Download error:', e.reason)
            if ntries > 0:
                if hasattr(e, 'code') and 500 <= e.code < 600:
                    # recursively retry 5xx HTTP errors
                    entry = (path, uri, fun, ntries - 1)
                    return FetchEntry(entry)
        if fun:
            run(fun, [path])
    return [path, fun]


@ExceptionLogger(None, ValueError, hlr.ch, "")
def callParallelFetchUrl(urls, nthreads):
    """
    Fetches Urls in parallel, urls must be an array of string sets
    e.g [('/pathtofiledownloaded.format', 'uri', 'decompression fun', 'ntries)]
    and if a decompressing function is given, it will be used
    """

    results = ThreadPool(nthreads).imap_unordered(FetchEntry, urls)
    for path in results:
        logger.info('Downloaded ' + path[0])
        if path[1]:
            logger.info('Extracted ' + path[0])


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
