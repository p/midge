# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Unittests for the application module.

Each test runs in its own TestConnection, which means that it has a
freshly created (and empty) database. This explains why the tests are
not as fast as one might hope.

"""
import mx.DateTime
import unittest

import midge.application as application
import midge.connection as connection
import midge.lib as lib


class BaseTest(unittest.TestCase):

    session_id = "session-id"

    def setUp(self, *args):
        self.connection = connection.TestConnection()
        self.app = application.Application(self.connection)

    def tearDown(self):
        self.connection.close()


class UserTests(BaseTest):

    def test_cannot_get_user_with_unknown_session_id(self):
        """Check cannot get user without session_id"""
        self.assertEqual(self.app.get_user(self.session_id), None)

    def test_cannot_logout_when_not_logged_in(self):
        """Check cannot logout when not logged in"""
        self.assertEqual(self.app.logout(self.session_id), False)

    def test_can_login_and_logout(self):
        """Check login and logout (once)"""
        self.assertEqual(self.app.login(self.session_id,
                                        "test-username",
                                        "test-password"), True)
        user = self.app.get_user(self.session_id)
        self.assertEqual(isinstance(user, application.User), True)
        self.assertEqual(self.app.logout(self.session_id), True)
        self.assertEqual(self.app.logout(self.session_id), False)

    def test_can_create_user(self):
        """Check create and login as a new user"""
        self.app.create_new_user("username with spaces",
                                 "name with a quote '",
                                 "timothy@corbettclark.com",
                                 "password'@$#")
        self.assertEqual(self.app.login(self.session_id,
                                        "username with spaces",
                                        "password'@$#"),
                         True)
        user = self.app.get_user(self.session_id)
        self.assertNotEqual(user, None)
        self.assertEqual(user.name, "name with a quote '")
        self.assertEqual(user.email, "timothy@corbettclark.com")
        self.assertEqual(user.username, "username with spaces")

    def test_cannot_create_two_users_of_same_username(self):
        """Check cannot create two users of the same username"""
        self.app.create_new_user("username", "name",
                                 "email", "password")
        self.failUnlessRaises(
            application.ValueInUseException,
            self.app.create_new_user,
            "username", "name", "email", "password")

    def test_cannot_get_user_once_session_expired(self):
        """Check cannot get user once session expired"""
        self.assertEqual(self.app.login(self.session_id,
                                        "test-username",
                                        "test-password"), True)
        user = self.app.get_user(self.session_id)
        self.assertEqual(isinstance(user, application.User), True)
        self.app.expired_session(self.session_id)
        self.assertEqual(user.user_id, None)
        user = self.app.get_user(self.session_id)
        self.assertEqual(user, None)

    def test_get_usernames(self):
        """Check get all usernames"""
        self.assertEqual(self.app.usernames, ["test-username"])
        self.app.create_new_user("another username",
                                 "full name",
                                 "email",
                                 "password")
        usernames = self.app.usernames
        usernames.sort()
        self.assertEqual(usernames, ["another username", "test-username"])
        

class StatusTests(BaseTest):

    def test_all_statuses(self):
        """Check all status values"""
        statuses = application.Statuses(self.connection)
        self.assertEqual(statuses.values,
                         ("new",
                          "reviewed",
                          "scheduled",
                          "fixed",
                          "closed"))

    def test_initial_status(self):
        """Check statuses table has an initial value"""
        statuses = application.Statuses(self.connection)
        self.assertEqual(statuses.initial_value, "new")
        

class CategoryTests(BaseTest):

    def test_category_starts_empty(self):
        """Check category starts blank"""
        self.assertEqual(len(self.app.categories), 1)
        self.assertEqual(self.app.categories[0], "")

    def _add_category(self, value):
        return self.app.bugs.categories.create_new_value(value)

    def test_can_add_categories(self):
        """Check create new categories"""
        self._add_category("foobar")
        self.assertEqual(len(self.app.categories), 2)
        self.assertEqual(self.app.categories[0], "")
        self.assertEqual(self.app.categories[1], "foobar")
        self.failUnlessRaises(
            application.ValueInUseException,
            self._add_category, "foobar")
        for invalid_value in ("fo'obar",
                              'fo"obar',
                              "fo\nobar",
                              "#"):
            self.failUnlessRaises(
                application.InvalidValueException,
                self._add_category, invalid_value)


class VersionTests(BaseTest):

    def test_versions_starts_empty(self):
        """Check version starts blank"""
        self.assertEqual(len(self.app.versions), 1)
        self.assertEqual(self.app.versions[0], "")


class KeywordTests(BaseTest):

    def test_keywords_starts_empty(self):
        """Check keyword starts blank"""
        self.assertEqual(len(self.app.keywords), 1)
        self.assertEqual(self.app.keywords[0], "")

        
class BugTests(BaseTest):

    TITLE = "a title '"
    VERSION = "a version"
    CATEGORY = "a category"
    DESCRIPTION = """some comments
                           on several lines"""

    def _add_bug(self):
        bug_id = self.app.add_bug(
            self.session_id,
            title=self.TITLE,
            version=self.VERSION,
            category=self.CATEGORY,
            description=self.DESCRIPTION)
        bug = self.app.get_bug(self.session_id, bug_id)
        return bug

    def _login(self):
        self.assertEqual(self.app.login(self.session_id,
                                        "test-username",
                                        "test-password"), True)
        user = self.app.get_user(self.session_id)
        self.assertNotEqual(user, None)
        return user

    def test_canot_get_bug(self):
        """Check unable to retrieve non-existant bug"""
        self._login()
        self.failUnlessRaises(
            application.NoSuchBugException,
            self.app.get_bug, self.session_id, -1)
        self.failUnlessRaises(
            application.NoSuchBugException,
            self.app.get_bug, self.session_id, "-1")
        self.failUnlessRaises(
            application.NoSuchBugException,
            self.app.get_bug, self.session_id, "asdf")

        self.assertEqual(self.app.logout(self.session_id), True)
        self.assertEqual(self.app.get_bug(self.session_id, 1), None)
        self.assertEqual(self.app.get_bug(self.session_id, -1), None)
        self.assertEqual(
            self.app.get_bug(self.session_id, "asdf"), None)

    def test_add_bug(self):
        """Check create new bug"""
        user = self._login()
        bug = self._add_bug()
        initial_status = application.Statuses(self.connection).initial_value
        self.assertEqual(bug.status, initial_status)
        self.assertEqual(bug.title, self.TITLE)
        self.assertEqual(bug.reported_in, self.VERSION)
        self.assertEqual(bug.fixed_in, "")
        self.assertEqual(bug.tested_ok_in, "")
        self.assertEqual(bug.user_id, user.user_id)
        self.assertEqual(isinstance(bug.date,
                                    type(mx.DateTime.DateTime(0))),
                         True)
        self.assertNotEqual(bug.comments, None)
        self.assertEqual(len(bug.comments), 1)
        comment = bug.comments[0]
        self.assertEqual(comment.text, self.DESCRIPTION)
        self.assertEqual(comment.users_name, user.name)
        self.assertEqual(comment.username, user.username)
        self.assertEqual(isinstance(comment.date,
                                    type(mx.DateTime.DateTime(0))),
                         True)

    def test_add_comments(self):
        """Check add comments to a bug"""
        user = self._login()
        bug = self._add_bug()
        bug.change(user, comment="more comments")
        self.assertEqual(len(bug.comments), 2)
        # As timestamps are only to the nearest second, the new
        # comment could be in one of two places.
        self.assert_("more comments" in (bug.comments[0].text, bug.comments[1].text))

    def test_change_status(self):
        """Check change bug status"""
        user = self._login()
        bug = self._add_bug()
        for status in self.app.statuses:
            bug.change(user, status=status)
            bug = self.app.get_bug(self.session_id, bug.bug_id)
            self.assertEqual(bug.status, status)
        self.failUnlessRaises(
            application.InvalidValueException,
            bug.change, user, status="this is not a valid status")

    def test_change_category(self):
        """Check change bug category"""
        user = self._login()
        bug = self._add_bug()
        self.assertEqual(bug.category, self.CATEGORY)
        bug.change(user, category="")
        bug = self.app.get_bug(self.session_id, bug.bug_id)
        self.assertEqual(bug.category, "")
        bug.change(user, category="")
        bug.change(user, category=self.CATEGORY)
        bug = self.app.get_bug(self.session_id, bug.bug_id)
        self.assertEqual(bug.category, self.CATEGORY)
        bug.change(user, category=self.CATEGORY)
        bug.change(user, category="a new category")
        bug = self.app.get_bug(self.session_id, bug.bug_id)
        self.assertEqual(bug.category, "a new category")
        bug.change(user, category="a new category")
        
    def test_list_new_bugs(self):
        """Check list of new bugs"""
        user = self._login()

        ids = {}
        for p in (2,1,5,4,3):
            bug = self._add_bug()
            bug.change(user, category=p)
            ids[p] = bug.bug_id

        bug = self._add_bug()
        bug.change(user, status="reviewed")
        
        search = application.Search(
            ("bug_id", "category", "reported_in", "title"),
            "category", "ascending", status="new")
        self.app.search(self.session_id, search)
        self.assertEqual(search.variables,
                         ("bug_id", "category", "reported_in", "title"))
        self.assertEqual(search.titles,
                         ("Bug", "Category", "Reported in", "Title"))
        self.assertEqual(len(search.rows), 5)

        index = 0
        for p in (1,2,3,4,5):
            row = search.rows[index]
            assert len(row) == 4
            assert len(row.get()) == 4
            self.assertEqual(row.bug_id, ids[p])
            self.assertEqual(row.category, str(p))
            self.assertEqual(row.reported_in, self.VERSION)
            self.assertEqual(row.title, self.TITLE)
            index += 1

    def test_list_reviewed_bugs(self):
        """Check list of reviewed bugs"""
        user = self._login()

        ids = {}
        for p in (2,1,5,4,3):
            bug = self._add_bug()
            bug.change(user, status="reviewed", priority=p)
            ids[p] = bug.bug_id

        bug = self._add_bug()
        bug.change(user, status="fixed")
            
        search = application.Search(
            ("bug_id", "priority", "category", "reported_in", "title"),
            "priority", "descending", status="reviewed")
        self.app.search(self.session_id, search)
        self.assertEqual(search.variables,
                         ("bug_id", "priority", "category",
                          "reported_in", "title"))
        self.assertEqual(search.titles,
                         ("Bug", "Priority", "Category",
                          "Reported in", "Title"))
        self.assertEqual(len(search.rows), 5)

        index = 0
        for p in (5,4,3,2,1):
            row = search.rows[index]
            assert len(row) == 5
            assert len(row.get()) == 5
            self.assertEqual(row.bug_id, ids[p])
            self.assertEqual(row.priority, str(p))
            self.assertEqual(row.category, self.CATEGORY)
            self.assertEqual(row.reported_in, self.VERSION)
            self.assertEqual(row.title, self.TITLE)
            index += 1

    def test_list_scheduled_bugs(self):
        """Check list of scheduled bugs"""
        user = self._login()

        ids = {}
        for p in (2,1,5,4,3):
            bug = self._add_bug()
            bug.change(user, status="scheduled", priority=p)
            ids[p] = bug.bug_id

        bug = self._add_bug()
        bug.change(user, status="fixed")

        search = application.Search(
            ("bug_id", "priority", "category", "reported_in", "title"),
            "priority", "descending", status="scheduled")
        self.app.search(self.session_id, search)
        self.assertEqual(search.variables,
                         ("bug_id", "priority", "category",
                          "reported_in", "title"))
        self.assertEqual(search.titles,
                         ("Bug", "Priority", "Category",
                          "Reported in", "Title"))
        self.assertEqual(len(search.rows), 5)

        index = 0
        for p in (5,4,3,2,1):
            row = search.rows[index]
            assert len(row) == 5
            assert len(row.get()) == 5
            self.assertEqual(row.bug_id, ids[p])
            self.assertEqual(row.priority, str(p))
            self.assertEqual(row.category, self.CATEGORY)
            self.assertEqual(row.reported_in, self.VERSION)
            self.assertEqual(row.title, self.TITLE)
            index += 1

    def test_list_fixed_bugs(self):
        """Check list of fixed bugs"""
        user = self._login()

        ids = {}
        for p in (2,1,5,4,3):
            bug = self._add_bug()
            bug.change(user, status="fixed", fixed_in=p)
            ids[p] = bug.bug_id

        bug = self._add_bug()

        search = application.Search(
            ("bug_id", "priority", "category", "fixed_in", "title"),
            "fixed_in", "ascending", status="fixed")
        self.app.search(self.session_id, search)
        self.assertEqual(search.variables,
                         ("bug_id", "priority", "category",
                          "fixed_in", "title"))
        self.assertEqual(search.titles,
                         ("Bug", "Priority", "Category",
                          "Fixed in", "Title"))
        self.assertEqual(len(search.rows), 5)

        index = 0
        for p in (1,2,3,4,5):
            row = search.rows[index]
            assert len(row) == 5
            assert len(row.get()) == 5
            self.assertEqual(row.bug_id, ids[p])
            self.assertEqual(row.priority, "")
            self.assertEqual(row.category, self.CATEGORY)
            self.assertEqual(row.fixed_in, str(p))
            self.assertEqual(row.title, self.TITLE)
            index += 1

    def test_list_closed_bugs(self):
        """Check list of closed bugs"""
        user = self._login()

        ids = {}
        for p in (2,1,5,4,3):
            bug = self._add_bug()
            bug.change(user, status="closed", tested_ok_in=p)
            ids[p] = bug.bug_id

        bug = self._add_bug()
        search = application.Search(
            ("bug_id", "priority", "category", "tested_ok_in", "title"),
            "tested_ok_in", "ascending", status="closed")
        self.app.search(self.session_id, search)
        self.assertEqual(search.variables,
                         ("bug_id", "priority", "category",
                          "tested_ok_in", "title"))
        self.assertEqual(search.titles,
                         ("Bug", "Priority", "Category",
                          "Tested ok in", "Title"))
        self.assertEqual(len(search.rows), 5)

        index = 0
        for p in (1,2,3,4,5):
            row = search.rows[index]
            assert len(row) == 5
            assert len(row.get()) == 5
            self.assertEqual(row.bug_id, ids[p])
            self.assertEqual(row.priority, "")
            self.assertEqual(row.category, self.CATEGORY)
            self.assertEqual(row.tested_ok_in, str(p))
            self.assertEqual(row.title, self.TITLE)
            index += 1

    def test_status_count(self):
        """Check count of bugs in each status"""
        user = self._login()
        count = self.app.get_status_counts(self.session_id)
        n_bugs_in_status = {"new": 4,
                            "reviewed": 2,
                            "scheduled": 3,
                            "fixed": 0,
                            "closed": 2}

        counts = self.app.get_status_counts(self.session_id)
        for status, count in n_bugs_in_status.iteritems():
            self.assertEqual(getattr(counts, status), 0)
        
        for status, count in n_bugs_in_status.iteritems():
            for i in range(count):
                bug = self._add_bug()
                bug.change(user, status=status)

        counts = self.app.get_status_counts(self.session_id)
        for status, count in n_bugs_in_status.iteritems():
            self.assertEqual(getattr(counts, status), count)
        
    def test_search(self):
        """Check search for bugs"""
        user = self._login()

        bugs = []
        bug_id = self.app.add_bug(
            self.session_id,
            title="first title",
            version="a version",
            category="a category",
            description="a description")
        bugs.append(self.app.get_bug(self.session_id, bug_id))
        bug_id = self.app.add_bug(
            self.session_id,
            title="foobar",
            version="a version",
            category="a category",
            description="second description")
        bugs.append(self.app.get_bug(self.session_id, bug_id))
        bug_id = self.app.add_bug(
            self.session_id,
            title="second title",
            version="another version",
            category="a category",
            description="something else")
        bugs.append(self.app.get_bug(self.session_id, bug_id))
        
        bugs[1].change(user, status="reviewed")
        bugs[2].change(user, comment="more comments")
        
        search = application.Search(("bug_id",), "bug_id", "ascending",
                                    status="new")
        self.app.search(self.session_id, search)
        self.assertEqual(len(search.rows), 2)
        
        search.criteria = {"status": "reviewed"}
        self.app.search(self.session_id, search)
        self.assertEqual(len(search.rows), 1)
        
        search.criteria = {"status_regex": "new|reviewed"}
        self.app.search(self.session_id, search)
        self.assertEqual(len(search.rows), 3)

        search.criteria = {"status_regex": ".*n.*"}
        self.app.search(self.session_id, search)
        self.assertEqual(len(search.rows), 2)

        search.criteria = {"title": "first title"}
        self.app.search(self.session_id, search)
        self.assertEqual(len(search.rows), 1)

        search.criteria = {"title": "foobar"}
        self.app.search(self.session_id, search)
        self.assertEqual(len(search.rows), 1)

        search.criteria = {"title": ".*title"}
        self.app.search(self.session_id, search)
        self.assertEqual(len(search.rows), 2)

        search.criteria = {"title": "'"}
        self.app.search(self.session_id, search)
        self.assertEqual(len(search.rows), 0)

        search.criteria = {"comments": ".*description"}
        self.app.search(self.session_id, search)
        self.assertEqual(len(search.rows), 2)
        
        search.criteria = {"comments": "something|comments"}
        self.app.search(self.session_id, search)
        self.assertEqual(len(search.rows), 1)
        
        search.criteria = {"comments": "description|comments"}
        self.app.search(self.session_id, search)
        self.assertEqual(len(search.rows), 3)
        
        search.criteria = {"comments": "'"}
        self.app.search(self.session_id, search)
        self.assertEqual(len(search.rows), 0)

        search.criteria = {"comments": "\\"}
        self.failUnlessRaises(
            application.InvalidSearchException,
            self.app.search,
            self.session_id, search)

        search.criteria = {"comments": "("}
        self.failUnlessRaises(
            application.InvalidSearchException,
            self.app.search,
            self.session_id, search)

        search.criteria = {"comments": "["}
        self.failUnlessRaises(
            application.InvalidSearchException,
            self.app.search,
            self.session_id, search)
