# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Unittests for the io module."""

import mx.DateTime
import unittest

import midge.application as application
import midge.connection as connection
import midge.io as io


class BaseTest(unittest.TestCase):

    def setUp(self, *args):
        self.connection = connection.TestConnection()
        self.importer = io.Importer(self.connection)

    def tearDown(self):
        self.connection.close()


class ImporterTests(BaseTest):

    def test_import_users(self):
        """Check import users"""
        users = [("username%d" %i, "Full name %d" %i,
                  "Email %d" %i, "Password %d" %i) for i in (1,2,3)]
        for username, name, email, password in users:
            self.importer.import_user(username, name, email, password)

        for username, name, email, password in users:
            user = self.importer.get_user(username)
            self.assertEqual(user.username, username)
            self.assertEqual(user.name, name)
            self.assertEqual(user.email, email)

    def _add_bug(self, user):
        bugs = application.Bugs(self.connection)
        bug_id = bugs.add(
            user,
            title="a title",
            version="a version",
            configuration="a configuration",
            category="a category",
            description="a description")
        bug = bugs.get(bug_id)
        return bug
        
    def test_import_comments(self):
        """Check import comment"""
        self.importer.import_user("username", "name", "email", "password")
        user = application.User(self.connection)
        user.login("username", "password")
        bug = self._add_bug(user)
        self.assertEqual(len(bug.comments), 1)
        comments = [("username", "Sun Apr 12 09:31:06 BST 2004",
                     str(bug.bug_id), "another comment"),
                    ("username", "Mon Apr 13 12:23:00 GMT 2000",
                     str(bug.bug_id), "a second comment")]
        for username, timestamp, bug_id, text in comments:
            self.importer.import_comment(username, timestamp, bug_id, text)
        self.assertEqual(len(bug.comments), 3)

        comment1 = bug.comments[1]
        self.assertEqual(comment1.username, "username")
        self.assertEqual(comment1.text, "another comment")

        comment2 = bug.comments[0]
        self.assertEqual(comment2.username, "username")
        self.assertEqual(comment2.text, "a second comment")

    def test_import_bugs(self):
        """Check import bugs"""
        self.importer.import_user("username", "name", "email", "password")
        self.importer.import_bug("username",
                                 "Mon Apr 13 12:23:00 GMT 2000",
                                 "23",
                                 "a title",
                                 "reviewed",
                                 "a category",
                                 "a configuration",
                                 "a reported_in",
                                 "",
                                 "a closed_in")

        bugs = application.Bugs(self.connection)
        bug = bugs.get(23)
        self.assertEqual(bug.title, "a title")
        self.assertEqual(bug.status, "reviewed")
        self.assertEqual(bug.category, "a category")
        self.assertEqual(bug.configuration, "a configuration")
        self.assertEqual(bug.reported_in, "a reported_in")
        self.assertEqual(bug.fixed_in, "")
        self.assertEqual(bug.closed_in, "a closed_in")
        self.assertEqual(len(bug.comments), 0)

        user = application.User(self.connection)
        user.login("username", "password")
        bug = self._add_bug(user)
        self.assertEqual(bug.bug_id, 24)
