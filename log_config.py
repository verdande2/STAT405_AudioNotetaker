"""
log_config.py

Helper functions to enable logging with the loguru package in my notebooks.

"""
from __future__ import annotations

import logging
import sys

from loguru import logger

# configurable constants
DEFAULT_DEPTH: int = 6
COLORS_ENABLED: bool = True


class InterceptHandler(logging.Handler):
    """
    Simple handler to redirect stdout logging to Loguru for prettier formatting.
    """

    def emit(self, record: logging.LogRecord) -> None:
        logger.opt(depth=DEFAULT_DEPTH,
                   exception=record.exc_info,
                   colors=COLORS_ENABLED,
                   ).log(record.levelname, record.getMessage())

    # might need this adapted function for deeper traceback?
    # def emit(self, record: logging.LogRecord) -> None:
    #     # Find the depth to the caller outside of logging machinery
    #     frame = inspect.currentframe()
    #     depth = 2  # default minimum
    #     while frame:
    #         if frame.f_code.co_filename != logging.__file__:
    #             break
    #         frame = frame.f_back
    #         depth += 1

    #     # Redirect to loguru
    #     logger.opt(depth=depth, exception=record.exc_info).log(record.levelname, record.getMessage())


def setup_logging(level: int = logging.INFO) -> None:
    """
    setup_logging(): This function sets up the logging configuration for the entire project. It sets up a handler to steal log output and forward to loguru, and then sets up loguru configuration.

    Args:
        level (int, optional): Minimum logging level (default: logging.INFO)
                               (one of [FATAL = CRITICAL > ERROR > WARN = WARNING > INFO > DEBUG > NOTSET] in descending priority)
    """
    setup_logging_handler(level) # first set up handler
    setup_loguru(level) # then configure loguru


def setup_logging_handler(level: int = logging.INFO) -> None:
    """
    Setup handler to steal log output and forward to loguru

    Args:
        level (int, optional): Minimum logging level (default: logging.INFO)
                               (one of [FATAL = CRITICAL > ERROR > WARN = WARNING > INFO > DEBUG > NOTSET] in descending priority)
    """
    # first, remove all existing logging handlers to avoid doubling up
    logging.root.handlers = []
    
    # now, we set the config for the standard logging package to our handler to "steal" the output and pretty it up for logging
    logging.basicConfig(handlers=[InterceptHandler()], level=level)


def setup_loguru(level: int = logging.INFO) -> None:
    """
    Clears any existing loggers and sets up a custom one via loguru

    Args:
        level (int): Minimum logging level (default: logging.INFO)
                     (one of [FATAL = CRITICAL > ERROR > WARN = WARNING > INFO > DEBUG > NOTSET] in descending priority)
    """
    # clear existing handlers, then add my own and pass along the intended min level
    logger.remove()

    # Add a new stderr handler with clean formatting
    logger.add(
        sys.stderr,
        level=level,
        colorize=True,
        # format=(
        #     "<green>{time:HH:mm:ss}</green> | "
        #     "<level>{level: <8}</level> | "
        #     "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        #     "<level>{message}</level>"
        # ),
        backtrace=True,  # shows full traceback
        diagnose=True,  # shows local variable values in exceptions
    )