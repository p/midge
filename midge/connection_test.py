# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Unittests for the connection module."""

import unittest

import midge.config as config
import midge.connection as connection


class ConnectionTests(unittest.TestCase):

    def test_connection(self):
        """Check open/close connection to the database."""
        config.read()
        conn = connection.Connection()
        conn.close()

    def test_test_connection(self):
        """Check open/close connection to the test database."""
        config.read()
        conn = connection.TestConnection()
        conn.close()
