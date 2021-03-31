"""
Adds thread-local context to a Python logger.
"""
import logging
import threading
from typing import Any, Callable, Mapping, Optional, Union

_EXTRA_TYPE = Mapping[str, Any]

_THREAD_LOCAL = threading.local()


_THREAD_LOCAL.extra = dict()


def get_extra() -> _EXTRA_TYPE:
    """
    Retrieve the thread-local extra.

    This initializes the thread-local variable if necessary.
    """
    try:
        return _THREAD_LOCAL.extra
    except AttributeError:
        _THREAD_LOCAL.extra = dict()
    return _THREAD_LOCAL.extra


def set_extra(extra: _EXTRA_TYPE) -> _EXTRA_TYPE:
    """
    Sets the thread-local context to a new value.

    Note that you will need to preserve and restore the old value
    if you don't want to permanently add the keys in this value.
    In that case, you would be better off using the context manager
    :py:class:`add_logging_context`.
    """
    _THREAD_LOCAL.extra = extra
    return _THREAD_LOCAL.extra


class Logger:
    """
    Wrapper for a python :py:class:`logging.Logger`.

    This wrapper reads the current local context and emits
    them for each log message.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        logger: Optional[Union[logging.Logger, "Logger"]] = None,
    ):
        """
        Initialize.

        Args:
            logger: A logging.Logger or ContextLogger instance to inherit
                from.
        """
        if isinstance(logger, Logger):
            self.base_logger: Any = logger.base_logger
        else:
            self.base_logger = logger or logging.getLogger(name=name)

    def _msg(self, func: Callable, msg, *args, **kwargs):
        """Log with our extra values,"""
        extra = {
            **self.extra,
            **kwargs.pop("extra", {}),
        }
        return func(msg, *args, extra=extra, **kwargs)

    @property
    def extra(self) -> _EXTRA_TYPE:
        """Return the extra metadata that this logger sends with every message."""
        return get_extra()

    def debug(self, msg, *args, **kwargs):
        """Debug."""
        return self._msg(self.base_logger.debug, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Info."""
        return self._msg(self.base_logger.info, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Warning."""
        return self._msg(self.base_logger.warning, msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        """Warn. Deprecated. Use `warning` instead."""
        return self._msg(self.base_logger.warn, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Error."""
        return self._msg(self.base_logger.error, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Critical."""
        return self._msg(self.base_logger.critical, msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        """Log."""
        return self._msg(self.base_logger.log, level, msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """Exception."""
        return self._msg(self.base_logger.exception, msg, *args, **kwargs)


class add_logging_context:
    """
    A context manager to push and pop "extra" dictionary keys.
    """

    def __init__(self, **kwargs):
        """Create a new context manager."""
        self._new_extra = kwargs
        self._old_extra = get_extra()

    def __enter__(self):
        """Add the new kwargs to the thread-local state."""
        self._old_extra = get_extra()
        set_extra({**_THREAD_LOCAL.extra, **self._new_extra})
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Return the thread-local state to what it used to be."""
        _THREAD_LOCAL.extra = set_extra(self._old_extra)
        return False
