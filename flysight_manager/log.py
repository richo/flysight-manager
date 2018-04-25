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
warn = make_logger("!")

def make_loggable(cls):
    name = cls.__name__
    def discard_self(func):
        return lambda _, *args, **kwargs: func(*args, **kwargs)

    cls.debug = discard_self(make_logger("* %s" % name, lambda: os.getenv("DEBUG")))
    cls.info = discard_self(make_logger("+ %s" % name))
    cls.warn = discard_self(make_logger("! %s" % name))
    def fatal(msg):
        discard_self(make_logger("! %s" % name)(msg))
        sys.exit(1)
    cls.fatal = fatal

    return cls

def catch_exceptions_and_retry(report):
    def outer(func):
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
                report.finish_with_exception(exc)
                report.send()
                raise exc

        return inner
    return outer


def catch_exceptions(report):
    def outer(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as e:
                if os.getenv("DEBUG"):
                    traceback.print_exc(e)
                report.finish_with_exception(e)
                report.send()
                fatal(e)
        return inner
    return outer
