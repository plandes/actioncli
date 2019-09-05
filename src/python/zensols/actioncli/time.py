"""Peformance measure convenience utils.

"""
__author__ = 'Paul Landes'

import logging
import inspect
import time as tm

time_logger = logging.getLogger(__name__)


class time(object):
    """Used in a ``with`` scope that executes the body and logs the elapsed time.

    Format f-strings are supported as the locals are taken from the calling
    frame on exit.  This means you can do things like:

        with time('processed {cnt} items'):
            cnt = 5
            tm.sleep(1)

    which produeces: ``processed 5 items``.

    See the initializer documentation about special treatment for global
    loggers.

    """
    def __init__(self, msg, level=logging.INFO, logger=None):
        """Create the time object.

        If a logger is not given, it is taken from the calling frame's global
        variable named ``logger``.  If this global doesn't exit it logs to
        standard out.

        You can force standard out instead of a logger by using 

        :param msg: the message log when exiting the closure
        :param logger: the logger to use for logging or the string ``stdout``
                       for printing to standard
        :param level: the level at which the message is logged

        """
        self.msg = msg
        self.logger = logger
        self.level = level
        frame = inspect.currentframe()
        try:
            globs = frame.f_back.f_globals
            if 'logger' in globs:
                self.logger = globs['logger']
        except Exception as e:
            time_logger.error(e)

    def __enter__(self):
        self.t0 = tm.time()

    def __exit__(self, type, value, traceback):
        elapse = tm.time() - self.t0
        msg = self.msg
        frame = inspect.currentframe()
        try:
            locals = frame.f_back.f_locals
            msg = msg.format(**locals)
        except Exception as e:
            time_logger.error(e)
        msgstr = f'{msg} in {elapse:.1f}s'
        if self.logger is not None:
            self.logger.log(self.level, msgstr)
        else:
            print(msgstr)
