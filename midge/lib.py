# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Common library routines."""

import smtplib
import socket
import time
import urllib
import xml.sax.saxutils

import midge.config as config
import midge.logger as logger


def join_url(path, dictionary=None):
    if dictionary:
        attr = "&".join(["%s=%s" % (key, urllib.quote_plus(value))
                         for key, value in dictionary.iteritems()])
        if "?" in path:
            return "%s&%s" % (path, attr)
        else:
            return "%s?%s" % (path, attr)
    else:
        return path


def split_url(url):
    values = {}
    if "?" in url:
        path, variable_value_pairs = url.split("?", 1)
        for variable_value in variable_value_pairs.split("&"):
            variable, value = variable_value.split("=")
            values[variable] = urllib.unquote_plus(value)
    else:
        path = url
    return path, values


def html_entity_escape(text):
    return xml.sax.saxutils.escape(text)


def format_date(date):
    return date.strftime("%a %d of %B, %Y")


def format_time(date):
    return date.strftime("%H:%M:%S")


def sendmail(to, message):
    """Attempt to send email, and return boolean success."""
    try:
        server = smtplib.SMTP(config.Email.smtp_host)
	from_to_headers = "From: %s\r\nTo: %s\r\n" % (
            config.Email.from_address, to)
        subject = "Subject: Midge password\r\n"
        server.sendmail(config.Email.from_address, [to],
                        subject + from_to_headers + "\r\n" + message)
        server.quit()
        return True
    except (smtplib.SMTPException, socket.error):
        logger.error("Unable to send email")
        logger.exception()
    return False
