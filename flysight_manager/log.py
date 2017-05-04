import os
import sys
import functools
import traceback


# Oh god why isn't there a standard package for this.
def make_logger(c, enabled=lambda: True):
    def inner(msg, args=()):
        if enabled():
            fmt = "[%s] %s" % (c, msg)
            # Cope gracefully with printf style invocations
            print(fmt % args)
    return inner


def fatal(msg):
    make_logger("!")(msg)
    sys.exit(1)
debug = make_logger("*", lambda: os.getenv("DEBUG"))
info = make_logger("+")


def catch_exceptions_and_retry(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        exc = None
        for i in range(3):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                exc = e
                info("Caught exception: %s, continuing" % (repr(e)))
        else:
            raise exc

    return inner


def catch_exceptions(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            if os.getenv("DEBUG"):
                traceback.print_exc(e)
            fatal(e)
    return inner
