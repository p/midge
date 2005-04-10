# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Functionality to import and export bugs from Midge."""

import csv

import midge.application as application


class Importer:

    def __init__(self, connection):
        self.connection = connection
        self.users = application.Users(connection)
        self.bugs = application.Bugs(connection)
        self.passwords = {}
        
    def _get_user(self, username):
        user = application.User(self.connection)
        user.login(username, self.passwords[username])
        return user

    def _import_user(self, username, name, email, password):
        self.users.create_new_user(username, name, email, password)
        self.passwords[username] = password

    def _import_bug(self, bug_id, username, timestamp, title, status,
                    priority, resolution,
                    category, keyword,
                    reported_in, fixed_in, tested_ok_in):
        user = self._get_user(username)
        self.bugs.import_bug(bug_id, user, timestamp, title, status,
                             priority, resolution,
                             category, keyword,
                             reported_in, fixed_in, tested_ok_in)

    def _import_comment(self, bug_id, username, timestamp, text):
        bug = self.bugs.get(bug_id)
        user = self._get_user(username)
        bug.change(user, log_changes=False, comment=text, timestamp=timestamp)

    def _import_users_from_file(self, filename):
        f = file(filename)
        reader = csv.reader(f)
        iterator = iter(reader)
        titles = iterator.next()
        assert titles == ["Username", "Name", "Email", "Password"]
        for row in iterator:
            self._import_user(*row)

    def _import_bugs_from_file(self, filename):
        f = file(filename)
        reader = csv.reader(f)
        iterator = iter(reader)
        titles = iterator.next()
        assert titles == ["Bug", "Username", "Date", "Title", "Status",
                          "Priority", "Resolution",
                          "Category", "Keyword",
                          "Reported in", "Fixed in", "Tested ok in"]
        for row in iterator:
            self._import_bug(*row)

    def _import_comments_from_file(self, filename):
        f = file(filename)
        reader = csv.reader(f)
        iterator = iter(reader)
        titles = iterator.next()
        assert titles == ["Bug", "Username", "Date", "Comment"]
        for row in iterator:
            self._import_comment(*row)

    def import_all(self, users_filename, bugs_filename, comments_filename):
        """Import a set of data into the database."""
        self._import_users_from_file(users_filename)
        self._import_bugs_from_file(bugs_filename)
        self._import_comments_from_file(comments_filename)


class Exporter:

    def __init__(self, connection):
        self.users = application.Users(connection)
        self.bugs = application.Bugs(connection)

    def _write_users_to_file(self, filename):
        f = file(filename, "w")
        writer = csv.writer(f)
        writer.writerows(self.users.export_users())
        f.close()

    def _write_bugs_to_file(self, filename):
        f = file(filename, "w")
        writer = csv.writer(f)
        writer.writerows(self.bugs.export_bugs())
        f.close()
     
    def _write_comments_to_file(self, filename):
        f = file(filename, "w")
        writer = csv.writer(f)
        writer.writerows(self.bugs.export_comments())
        f.close()

    def export_all(self, users_filename, bugs_filename, comments_filename):
        """Export all bugs to three files (users, bugs, comments)."""
        self._write_users_to_file(users_filename)
        self._write_bugs_to_file(bugs_filename)
        self._write_comments_to_file(comments_filename)           
