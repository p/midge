# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Functionality to import and export bugs from Midge."""

import midge.application as application


class Importer:

    def __init__(self, connection):
        self.connection = connection
        self.users = application.Users(connection)
        self.bugs = application.Bugs(connection)
        self.passwords = {}
        
    def get_user(self, username):
        user = application.User(self.connection)
        user.login(username, self.passwords[username])
        return user

    def import_user(self, username, name, email, password):
        self.users.create_new_user(username, name, email, password)
        self.passwords[username] = password

    def import_bug(self, username, timestamp, bug_id, title, status, category,
                   configuration, reported_in, fixed_in, closed_in):
        user = self.get_user(username)
        self.bugs.import_bug(user, timestamp, bug_id, title, status, category,
                         configuration, reported_in, fixed_in, closed_in)

    def import_comment(self, username, timestamp, bug_id, text):
        bug = self.bugs.get(bug_id)
        user = self.get_user(username)
        bug.change(user, comment=text, timestamp=timestamp)

    def import_all(self, users, bugs, comments):
        """Import a set of data into the database.

        The users, bugs, comments arguments are all lists of values
        which must correspond to the arguments of the import_user,
        import_bug, import_comment methods respectively.

        """
        for user in users:
            self.import_user(*user)
            
        for bug in bugs:
            self.import_bug(*bug)

        for comment in comments:
            self.import_comment(*comment)


class Exporter:

    pass
