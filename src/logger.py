"""
Structured logging — single setup call, used everywhere.
"""

import logging
import os
import sys

LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.WARNING),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
