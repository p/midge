# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Wrapper around syslog."""

import logging
import logging.handlers
import sys
import traceback

import midge.config


SYSLOG_PORT = 514


_logger = None
_handler = None

def start(debugging=False):
    global _logger, _handler
    if not _logger:
        _logger = logging.getLogger("midge")
        _handler = logging.handlers.SysLogHandler(
            (midge.config.Logging.host, SYSLOG_PORT), midge.config.Logging.facility)
        formatter = logging.Formatter('[%(name)s] %(message)s')
        _handler.setFormatter(formatter)
        _logger.addHandler(_handler)
        if debugging:
            _logger.setLevel(logging.DEBUG)
        else:
            _logger.setLevel(logging.INFO)

def stop():
    global _logger, _handler
    if _handler:
        _handler.close()
    _logger = None
    _handler = None

def _format_log_message(message, prefix=""):
    lines = []
    for line in message.split("\n"):
        if line:
            if prefix:
                lines.append("%s %s" % (prefix, line))
            else:
                lines.append(line)
    return "\n".join(lines)                          

def debug(message):
    if _logger:
        _logger.debug(_format_log_message(message))

def info(message):
    if _logger:
        _logger.info(_format_log_message(message))

def warn(message):
    if _logger:
        _logger.info(_format_log_message(message, "WARNING"))

def error(message):
    if message.startswith("ERROR:"):
        message = message[len("ERROR:"):]
        message = message.strip()
    if _logger:
        _logger.error(_format_log_message(message, "ERROR"))

def get_exception_as_lines():
    orig_lines = traceback.format_exception(*sys.exc_info())
    lines = []
    for orig_line in orig_lines:
        for line in orig_line.split("\n"):
            if line.strip():
                lines.append(line)
    return lines

def exception():
    lines = get_exception_as_lines()
    for line in lines:
        error(line)    
