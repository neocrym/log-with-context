"""
Adds thread-local context to a Python logger.
"""
import collections
import logging
import os
import threading
from types import TracebackType
from typing import Any, Callable, DefaultDict, Mapping, Optional, Type, Union

from typing_extensions import Literal

_EXTRA_TYPE = Mapping[str, Any]

_THREAD_LOCAL = threading.local()

_THREAD_LOCAL.pids = collections.defaultdict(dict)


def init_extra() -> None:
    """Initialize our thread-local variable for storing contexts."""
    if not hasattr(_THREAD_LOCAL, "pids"):
        _THREAD_LOCAL.pids = collections.defaultdict(dict)


def get_extra() -> _EXTRA_TYPE:
    """
    Retrieve the thread-local extra.

    This initializes the thread-local variable if necessary.
    """
    init_extra()
    pid = os.getpid()
    pids: Mapping[int, _EXTRA_TYPE] = _THREAD_LOCAL.pids
    return pids[pid]


def set_extra(extra: _EXTRA_TYPE) -> _EXTRA_TYPE:
    """
    Sets the thread-local context to a new value.

    This erases whatever the context used to be. If you would rather
    restore that old value later, you might prefer using the
    :py:class:`add_logging_context` context manager.
    """
    init_extra()
    pid = os.getpid()
    pids: DefaultDict[int, _EXTRA_TYPE] = _THREAD_LOCAL.pids
    pids[pid] = extra
    return pids[pid]


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
            logger: A logging.Logger instance to wrap.
        """
        if isinstance(logger, Logger):
            self.base_logger: Any = logger.base_logger
        else:
            self.base_logger = logger or logging.getLogger(name=name)

    def _msg(
        self, func: Callable[..., None], msg: Any, *args: Any, **kwargs: Any
    ) -> None:
        """Log with our extra values,"""
        extra = {
            **self.extra,
            **kwargs.pop("extra", {}),
        }
        # Because we wrap a logging.Logger instance through 2 layers
        # of redirection, we need to add 2 to the logger's stacklevel
        # so we correctly log the logging statement's line number and function name
        original_stacklevel = kwargs.pop("stacklevel", 1)
        stacklevel = original_stacklevel + 2
        return func(msg, *args, extra=extra, stacklevel=stacklevel, **kwargs)

    @property
    def extra(self) -> _EXTRA_TYPE:
        """Return the extra metadata that this logger sends with every message."""
        return get_extra()

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Debug."""
        return self._msg(self.base_logger.debug, msg, *args, **kwargs)

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Info."""
        return self._msg(self.base_logger.info, msg, *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Warning."""
        return self._msg(self.base_logger.warning, msg, *args, **kwargs)

    def warn(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Warn. Deprecated. Use `warning` instead."""
        return self._msg(self.base_logger.warn, msg, *args, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Error."""
        return self._msg(self.base_logger.error, msg, *args, **kwargs)

    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Critical."""
        return self._msg(self.base_logger.critical, msg, *args, **kwargs)

    def log(self, level: int, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log."""
        return self._msg(self.base_logger.log, level, msg, *args, **kwargs)

    def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Exception."""
        return self._msg(self.base_logger.exception, msg, *args, **kwargs)


class add_logging_context:
    """
    A context manager to push and pop "extra" dictionary keys.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Create a new context manager."""
        self._new_extra = kwargs
        self._old_extra: Mapping[str, Any] = {}

    def __enter__(self) -> "add_logging_context":
        """Add the new kwargs to the thread-local state."""
        self._old_extra = get_extra()
        set_extra({**self._old_extra, **self._new_extra})
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType] = None,
    ) -> Literal[False]:
        """Return the thread-local state to what it used to be."""
        set_extra(self._old_extra)
        return False
