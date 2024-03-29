# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Unittests for the administration module."""

import psycopg2
import unittest

import midge.administration as administration
import midge.config as config
import midge.lib as lib


class AdministrationTests(unittest.TestCase):

    def setUp(self):
        config.read()
        administration.create_tables(config.Database.test_name)
        self.connection = psycopg2.connect(
            "dbname=%s user=%s password=%s" % (config.Database.test_name,
                                               config.Database.user,
                                               config.Database.password))

    def tearDown(self):
        self.connection.close()
        administration.drop_tables(config.Database.test_name)

    def test_statuses_table(self):
        """Check status values in statuses table"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM statuses ORDER BY status_id;")
        ans = cursor.fetchall()
        cursor.close()
        self.assertEqual(ans,
                         [(status,) for status in ("new",
                                                   "reviewed",
                                                   "scheduled",
                                                   "fixed",
                                                   "closed")])

    def test_create_destroy_table(self):
        """Check create and destroy tables"""
        cursor = self.connection.cursor()

        cursor.execute("SELECT * FROM keyword_values;")
        self.assertEqual(len(cursor.fetchall()), 0)

        cursor.execute("SELECT * FROM resolution_values;")
        self.assertEqual(len(cursor.fetchall()), 0)

        cursor.execute("SELECT * FROM category_values;")
        self.assertEqual(len(cursor.fetchall()), 0)

        cursor.execute("SELECT * FROM versions;")
        self.assertEqual(len(cursor.fetchall()), 0)
       
        cursor.execute("SELECT * FROM reported_ins;")
        self.assertEqual(len(cursor.fetchall()), 0)
       
        cursor.execute("SELECT * FROM fixed_ins;")
        self.assertEqual(len(cursor.fetchall()), 0)
       
        cursor.execute("SELECT * FROM tested_ok_ins;")
        self.assertEqual(len(cursor.fetchall()), 0)

        cursor.execute("SELECT * FROM changes;")
        self.assertEqual(len(cursor.fetchall()), 0)
       
        cursor.execute("SELECT * FROM progress;")
        self.assertEqual(len(cursor.fetchall()), 0)
       
        cursor.close()
