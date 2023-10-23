"""Unit tests for :py:mod:`log_with_context`."""

import concurrent.futures
import logging
import unittest
import unittest.mock
from typing import Any

from log_with_context import Logger, add_logging_context

LOGGER = logging.getLogger()

LOG_METHOD_NAMES = [
    "debug",
    "info",
    "warning",
    "warn",
    "error",
    "critical",
    "exception",
]


def process_worker(val: Any) -> None:
    """See how our logger interacts with multiprocessing."""
    base_logger = unittest.mock.Mock(spec=LOGGER)
    logger = Logger(logger=base_logger)

    logger.debug("1")
    base_logger.debug.assert_called_with("1", extra={}, stacklevel=3)
    with add_logging_context(val=val):
        logger.debug("2")
        base_logger.debug.assert_called_with("2", extra=dict(val=val), stacklevel=3)


class TestLogger(unittest.TestCase):
    """Unit tests for :py:class:`log_with_context.Logger`."""

    def setUp(self) -> None:
        self.base_logger = unittest.mock.Mock(spec=LOGGER)
        self.logger = Logger(logger=self.base_logger)

    def gl(self, method_name: str) -> Any:
        """Execute a given method on our test logger."""
        return getattr(self.logger, method_name)

    def gb(self, method_name: str) -> Any:
        """Execute a given method on our base logger mock."""
        return getattr(self.base_logger, method_name)

    def test_add_logging_context(self) -> None:
        """Test that :py:class:`add_logging_context` works."""
        for method_name in LOG_METHOD_NAMES:
            with self.subTest(name=f"logger.{method_name}"):
                self.gl(method_name)("1")
                self.gb(method_name).assert_called_with("1", extra={}, stacklevel=3)

                with add_logging_context(a=1):
                    self.gl(method_name)("2")
                    self.gb(method_name).assert_called_with(
                        "2", extra=dict(a=1), stacklevel=3
                    )

                    with add_logging_context(b=2):
                        self.gl(method_name)("3")
                        self.gb(method_name).assert_called_with(
                            "3", extra=dict(a=1, b=2), stacklevel=3
                        )

                        with add_logging_context(a=4, c=3):
                            self.gl(method_name)("4")
                            self.gb(method_name).assert_called_with(
                                "4", extra=dict(a=4, b=2, c=3), stacklevel=3
                            )

                        self.gl(method_name)("5")
                        self.gb(method_name).assert_called_with(
                            "5", extra=dict(a=1, b=2), stacklevel=3
                        )

                    self.gl(method_name)("6")
                    self.gb(method_name).assert_called_with(
                        "6", extra=dict(a=1), stacklevel=3
                    )

                self.gl(method_name)("7")
                self.gb(method_name).assert_called_with("7", extra={}, stacklevel=3)

            self.gl(method_name)("8")
            self.gb(method_name).assert_called_with("8", extra={}, stacklevel=3)

    def test_inline_extra(self) -> None:
        """Test that we can add one-off additions to our context."""
        for method_name in LOG_METHOD_NAMES:
            with self.subTest(name=f"logger.{method_name}"):
                self.gl(method_name)("%s", method_name, extra=dict(hello=method_name))
                self.gb(method_name).assert_called_with(
                    "%s", method_name, extra=dict(hello=method_name), stacklevel=3
                )

    def test_thread_local(self) -> None:
        """Test that our logging context is indeed thread-local."""

        def thread_worker(val: Any) -> None:
            self.logger.debug("1")
            self.base_logger.debug.assert_called_with("1", extra={}, stacklevel=3)
            with add_logging_context(val=val):
                self.logger.debug("2")
                self.base_logger.debug.assert_called_with(
                    "2", extra=dict(val=val), stacklevel=3
                )

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as exc:
            with add_logging_context(a=1):
                list(exc.map(thread_worker, [1, 2]))

    def test_process_local(self) -> None:
        """Test how our logger works with multiple processes."""
        with concurrent.futures.ProcessPoolExecutor(max_workers=2) as exc:
            with add_logging_context(a=1):
                list(exc.map(process_worker, [1, 2]))

    def test_extra_without_add_logging_context(self) -> None:
        """
        Test that we can assign an initial extra value
        when we initialize the logger.
        """
        base_logger = unittest.mock.Mock(spec=LOGGER)
        logger = Logger(logger=base_logger, initial_extra=dict(a=1))
        self.assertEqual(logger.extra, dict(a=1))
        self.assertEqual(self.logger.extra, dict())
        logger.debug("1")
        base_logger.debug.assert_called_with("1", extra=dict(a=1), stacklevel=3)
        with add_logging_context(b=2):
            self.assertEqual(logger.extra, dict(a=1, b=2))
            self.assertEqual(self.logger.extra, dict(b=2))
            logger.info("2")
            base_logger.info.assert_called_with("2", extra=dict(a=1, b=2), stacklevel=3)
            with add_logging_context(c=3):
                self.assertEqual(logger.extra, dict(a=1, b=2, c=3))
                self.assertEqual(self.logger.extra, dict(b=2, c=3))
                logger.info("3")
                base_logger.info.assert_called_with(
                    "3", extra=dict(a=1, b=2, c=3), stacklevel=3
                )
                logger.info("4", extra=dict(d=4))
                base_logger.info.assert_called_with(
                    "4", extra=dict(a=1, b=2, c=3, d=4), stacklevel=3
                )
