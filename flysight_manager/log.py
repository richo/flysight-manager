import os
import sys
import functools
import traceback


class Log(object):
    OUTPUT = sys.stdout


def suppress_logs():
    Log.OUTPUT = open(os.devnull, 'w')


class LogAggregator(object):
    logs = None

    @classmethod
    def new(cls):
        cls.logs = []
        return cls.logs

    @classmethod
    def add(cls, l):
        if cls.logs is not None:
            return cls.logs.append(l)


# Oh god why isn't there a standard package for this.
def make_logger(c, enabled=lambda: True):
    def inner(msg, args=()):
        if enabled():
            fmt = "[%s] %s" % (c, msg)
            LogAggregator.add(fmt % args)
            Log.OUTPUT.write(fmt % args)
            Log.OUTPUT.write("\n")
            Log.OUTPUT.flush()
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
                    ret = func(*args, **kwargs)
                    report.finish()
                    report.send()
                    return ret
                except KeyboardInterrupt:
                    report.finish_with_reason("Interrupted at terminal")
                    report.send()
                    fatal("Interrupted at terminal")
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
                ret = func(*args, **kwargs)
                report.finish()
                report.send()
                return ret
            except KeyboardInterrupt:
                report.finish_with_reason("Interrupted at terminal")
                report.send()
                fatal("Interrupted at terminal")
            except Exception as e:
                if os.getenv("DEBUG"):
                    traceback.print_exc(e)
                report.finish_with_exception(e)
                report.send()
                fatal(e)
        return inner
    return outer
