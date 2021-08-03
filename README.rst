log-with-context--a thread-local, context-preserving Python logger
==================================================================

``log-with-context`` is a Python logger that saves variables in a
thread-local context to be passed as `extra` to Python
`logging <https://docs.python.org/3/library/logging.html>`_ methods.

Installation
------------

This library is available on PyPI and can be installed with

.. code:: bash

    python3 -m pip install log-with-context

Usage
-----

This library provides a wrapped Python logging.Logger that
adds a shared context to each logging message, passed as
the `extra` parameter.

**You will need an additional library** (like
`JSON-log-formatter <https://pypi.org/project/JSON-log-formatter/>`_)
**to actually output the logging messages**. We avoided putting this
functionality in this library to keep it lightweight and flexible.
We assumed that you already have a preferred way to format your
logging messages.

.. code:: python

    import logging
    import logging.config

    from log_with_context import add_logging_context, Logger

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "json": {"()": "json_log_formatter.JSONFormatter"},
        },
        "handlers": {
            "console": {
                "formatter": "json",
                "class": "logging.StreamHandler",
            }
        },
        "loggers": {
            "": {"handlers": ["console"], "level": "INFO"},
        },
    })

    LOGGER = Logger(__name__)

    LOGGER.info("First message. No context")

    with add_logging_context(current_request="hi"):
        LOGGER.info("Level 1")

        with add_logging_context(more_info="this"):
            LOGGER.warning("Level 2")

        LOGGER.info("Back to level 1")

    LOGGER.error("No context at all...")


The above program logs the following messages to standard error:

.. code:: json

    {"message": "First message. No context", "time": "2021-04-08T16:37:23.126099"}
    {"current_request": "hi", "message": "Level 1", "time": "2021-04-08T16:37:23.126336"}
    {"current_request": "hi", "more_info": "this", "message": "Level 2", "time": "2021-04-08T16:37:23.126389"}
    {"current_request": "hi", "message": "Back to level 1", "time": "2021-04-08T16:37:23.126457"}
    {"message": "No context at all...", "time": "2021-04-08T16:37:23.126514"}


This example may look trivial, but it is very handy to maintain a
logging context up and down a Python call stack without having
to pass additional variables to the functions and methods
that you call.

Implementation details
----------------------
Logging contexts are stored as thread-local variables. If you want
to share information between threads, you must create a Logging
context in each thread with the same information.

Similarly, logging contexts are *deliberately not copied* when
creating subprocesses. This is done to minimize bugs and make sure
that log-with-context behaves in the exact same manner across
operating systems.
