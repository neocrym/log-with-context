log-with-context--a thread-local, context-preserving Python logger
==================================================================

TODO: Fill out this logger

Logging contexts are stored as thread-local variables. If you want
to share information between threads, you must create a Logging
context in each thread with the same information.

Similarly, logging contexts are *deliberately not copied* when
creating subprocesses. This is done to minimize bugs and make sure
that log-with-context behaves in the exact same manner across
operating systems.
