"""Structured-ish logging: one line per event, key=value pairs, UTC timestamps."""

from __future__ import annotations

import logging
import os
import sys
import time


class _UTCFormatter(logging.Formatter):
    converter = time.gmtime


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logging.getLogger().handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_UTCFormatter("%(asctime)sZ %(levelname)s %(name)s %(message)s", "%Y-%m-%dT%H:%M:%S"))
        root = logging.getLogger()
        root.addHandler(handler)
        root.setLevel(os.environ.get("NBA_EDGE_LOG_LEVEL", "INFO"))
    return logger


def kv(**kwargs) -> str:
    return " ".join(f"{k}={v}" for k, v in kwargs.items())
