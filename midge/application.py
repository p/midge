# $Id$
# (C) Timothy Corbett-Clark, 2004

"""The main bugtracking application with concepts of users, bugs, etc."""

import re

import midge.connection as connection
import midge.lib as lib
import midge.logger as logger


class MidgeException(Exception):
    pass


class BugException(MidgeException):

    def __init__(self, bug_id):
        self.bug_id = bug_id
        MidgeException.__init__(self)

class NoSuchBugException(BugException):
    pass

class UnableToReadCommentsException(BugException):
    pass
    

class ValueInUseException(MidgeException):
    pass

class InvalidValueException(MidgeException):
    pass



class User(object):

    """Represent a user who may or may not be logged-in.

    The user attributes are all obtained live from the database, so it
    is ok to keep hold of a User instance for as long as is
    convenient.

    """
    def __init__(self, connection, username=None):
        self.connection = connection
        self.user_id = None
        if username:
            self.user_id = self._get_user_id(username)
        
    def _get_user_id(self, username):
        user_id = None
        username = lib.quote(username)
        cursor = self.connection.cursor()
        cursor.execute("""
                SELECT user_id FROM users
                WHERE username='%s';
                """ % username)
        ans = cursor.fetchone()
        if ans is not None:
            user_id = ans[0]
        cursor.close()
        return user_id

    def authenticate(self, password):
        assert self.user_id
        password = lib.quote(password)
        cursor = self.connection.cursor()
        cursor.execute("""
                SELECT * FROM users
                WHERE user_id=%d AND password='%s';
                """ % (self.user_id, password))
        ans = cursor.fetchone()
        authenticated = ans is not None
        cursor.close()
        return authenticated

    def get_password(self):
        if self.user_id is not None:
            return lib.unquote(self._get_attribute("password"))
        return None

    def set_password(self, password):
        if self.user_id is not None:
            password = lib.quote(password)
            return self._set_attribute("password", password)
        return False

    password = property(get_password, set_password)

    def _get_attribute(self, attribute):
        assert self.user_id
        value = None
        cursor = self.connection.cursor()
        cursor.execute("""
                SELECT %s FROM users
                WHERE user_id=%d;
                """ % (attribute, self.user_id))
        ans = cursor.fetchone()
        if ans is not None:
            value = lib.unquote(ans[0])
        cursor.close()
        return value

    def _set_attribute(self, attribute, value):
        assert self.user_id
        value = lib.quote(value)
        cursor = self.connection.cursor()
        cursor.execute("""
                UPDATE users SET %s='%s'
                WHERE user_id=%d;
                """ % (attribute, value, self.user_id))
        self.connection.commit()
        cursor.close()
        return True

    def get_username(self):
        if self.user_id is not None:
            return self._get_attribute("username")
        return None

    username = property(get_username)

    def get_name(self):
        if self.user_id is not None:
            return self._get_attribute("name")
        return None

    def set_name(self, name):
        if self.user_id is not None:
            return self._set_attribute("name", name)
        return False

    name = property(get_name, set_name)

    def get_email(self):
        if self.user_id is not None:
            return self._get_attribute("email")
        return None

    def set_email(self, email):
        if self.user_id is not None:
            return self._set_attribute("email", email)
        return False

    email = property(get_email, set_email)

    def login(self, username, password):
        self.logout()
        self.user_id = self._get_user_id(username)
        if self.user_id is not None:
            if not self.authenticate(password):
                self.user_id = None
        return self.user_id is not None

    def logout(self):
        self.user_id = None


class Users(object):

    """Access to all operations relating to users."""

    def __init__(self, connection):
        self.connection = connection
        self.logged_in_users = {}

    def expired_session(self, session_id):
        user = self.logged_in_users.get(session_id, None)
        if user is not None:
            logger.info('"Timeout of user "%s"' % user.username)
            user.logout()
            del self.logged_in_users[session_id]

    def create_new_user(self, username, name, email, password):
        cursor = self.connection.cursor()
        username = lib.quote(username)
        name = lib.quote(name)
        email = lib.quote(email)
        password = lib.quote(password)
        try:
            cursor.execute("""
                INSERT INTO users (username, password, name, email)
                       VALUES ('%s', '%s', '%s', '%s');
                       """ % (username, password, name, email))
            self.connection.commit()
        except connection.IntegrityError:
            # Almost certainly caused by username in use.
            self.connection.rollback()
            cursor.close()
            raise ValueInUseException
        cursor.close()
            
    def login(self, session_id, username, password):
        user = User(self.connection)
        if user.login(username, password):
            self.logged_in_users[session_id] = user
            logger.info('Logging in user "%s" under session: %s' % (
                user.username, session_id))
            return True
        else:
            logger.info('Failed login attempt for user "%s"' % username)
            return False

    def logout(self, session_id):
        user = self.logged_in_users.get(session_id, None)
        if user is not None:
            logger.info('Logged out user "%s" under session: %s' % (
                user.username, session_id))
            user.logout()
            del self.logged_in_users[session_id]
            return True
        else:
            return False

    def get_user(self, session_id):
        return self.logged_in_users.get(session_id, None)

    def _get_usernames(self):
        cursor = self.connection.cursor()
        cursor.execute("""
                SELECT username FROM users;
                """)
        usernames = [lib.unquote(row[0]) for row in cursor.fetchall()]
        return usernames

    usernames = property(_get_usernames)

    def email_password(self, username):
        user = User(self.connection, username)
        if user.username != username:
            raise NoSuchUsernameException, username
        return lib.sendmail(
            user.email, 'Your Midge password is "%s".' % user.password)
    

class Comment:

    """A single comment for a particular bug, cached from the database."""

    def __init__(self, bug_id, users_name, username, date, text):
        self.bug_id = bug_id
        self.users_name = users_name
        self.username = username
        self.date = date
        self.text = text


class Comments(list):

    """A list of comments for a particular bug, cached from the database."""

    def __init__(self, connection, bug_id):
        list.__init__(self)
        self.connection = connection
        self.bug_id = bug_id
        self._read_comments_from_database()
        
    def _read_comments_from_database(self):
        cursor = self.connection.cursor()
        cursor.execute("""
                SELECT users.name, users.username, date, comment
                FROM comments, users
                WHERE bug_id=%d
                AND comments.user_id = users.user_id
                ORDER BY date ASC;
                """ % self.bug_id)
        results = cursor.fetchall()
        cursor.close()
        if results is not None:
            for result in results:
                users_name, username, date, text = result
                text = lib.unquote(text)
                users_name = lib.unquote(users_name)
                username = lib.unquote(username)
                self.append(Comment(self.bug_id,
                                    users_name,
                                    username,
                                    date,
                                    text))
        else:
            raise UnableToReadCommentsException, self.bug_id
        
    def add(self, cursor, user, text, timestamp="now"):
        text = lib.quote(text.strip())
        cursor.execute("""
                INSERT INTO comments (bug_id, user_id, date, comment)
                       VALUES (%d, %d, '%s', '%s');
                """ % (self.bug_id, user.user_id, timestamp, text))

    

class Statuses(object):

    """All operations relating to bug statuses.

    Note Statuses is not a StateTable, as every bug must have a
    non-null status. Thus the underlying bugs table links to an entry
    in the statuses table, in contrast to every type of StateTable
    which link the other way (from state table to the bugs table).
    
    """
    def __init__(self, connection):
        self.connection = connection
        self._values = None
        self._initial_value = None
        self._initial_id = None

    def _get_values(self):
        """Return all the statuses in a sensible order."""
        if self._values is None:
            cursor = self.connection.cursor()
            cursor.execute("""
                    SELECT name
                    FROM statuses
                    ORDER BY status_id;
                    """)
            ans = cursor.fetchall()
            cursor.close()
            self._values = tuple([status for (status,) in ans])
        return self._values

    values = property(_get_values)

    def _get_initial_value(self):
        """Return the initial status which all bugs assume."""
        if self._initial_value is None:
            cursor = self.connection.cursor()
            cursor.execute("""
                    SELECT name
                    FROM statuses
                    ORDER BY status_id
                    LIMIT 1;
                    """)
            ans = cursor.fetchall()
            cursor.close()
            self._initial_value = ans[0][0]
        return self._initial_value

    initial_value = property(_get_initial_value)

    def _get_initial_id(self):
        """Return the id of the status which all bugs assume initially."""
        if self._initial_id is None:
            cursor = self.connection.cursor()
            cursor.execute("""
                    SELECT status_id
                    FROM statuses
                    ORDER BY status_id
                    LIMIT 1;
                    """)
            ans = cursor.fetchall()
            cursor.close()
            self._initial_id = ans[0][0]
        return self._initial_id

    initial_id = property(_get_initial_id)

    def set_for_bug(self, cursor, bug_id, status):
        try:
            cursor.execute("""
            UPDATE bugs
            SET status_id = (
                SELECT status_id
                FROM statuses
                WHERE name = '%s'
                )
            WHERE bug_id = %d;
            """ % (status, bug_id))
        except connection.IntegrityError:
            raise InvalidValueException


class StateTable(object):

    """Abstract behaviour of all optional bug states."""

    # These need to be provided by subclasses.
    valid_value = None
    bug_table = None
    value_table = None
    alphabetical = True
    
    def __init__(self, connection):
        self.connection = connection

    def _get_values(self):
        """Return a list of all existing values."""
        cursor = self.connection.cursor()
        if self.alphabetical:
            sort_column = "name"
        else:
            sort_column = "id"
        cursor.execute("""
                SELECT name
                FROM %(value_table)s
                ORDER BY %(sort_column)s;
                """ % {"value_table":self.value_table,
                       "sort_column":sort_column})
        ans = cursor.fetchall()
        cursor.close()
        values = [name for (name,) in ans]
        values.insert(0, "")
        return tuple(values)

    values = property(_get_values)

    def create_new_value(self, value):
        """Create a new value or raise if invalid."""
        if not self.valid_value.match(value):
            raise InvalidValueException, value
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO %(value_table)s (name)
                VALUES ('%(value)s');                 
                """ % {"value_table":self.value_table, "value":value})
            self.connection.commit()
        except connection.IntegrityError:
            self.connection.rollback()
            cursor.close()
            raise ValueInUseException
        cursor.close()

    def purge(self, names):
        """Remove all values not used by any name in a bug"""

    def get_for_bug(self, cursor, bug_id):
        """Return one of the values for a given bug (may be "").

        Not normally needed, as all the values are in the Bug
        object.
        
        """
        cursor.execute("""
                SELECT name
                FROM %(bug_table)s, %(value_table)s
                WHERE bug_id = %(bug_id)d AND
                      %(value_table)s.id = %(bug_table)s.id;
                """ % {"bug_table":self.bug_table,
                       "value_table":self.value_table,
                       "bug_id":bug_id})
        ans = cursor.fetchone()
        if ans:
            return ans[0]
        else:
            return ""

    def set_for_bug(self, cursor, bug_id, value):
        """Change one of the values for a given bug.

        Will create a new value if necessary.
        
        """
        if value:
            value = str(value)
            if not self.valid_value.match(value):
                raise InvalidValueException, value
            state_id = self._get_id(cursor, value)
            if not state_id:
                self.create_new_value(value)
                state_id = self._get_id(cursor, value)
            if self.get_for_bug(cursor, bug_id):
                self._update_for_bug(cursor, bug_id, state_id)
            else:
                self._insert_for_bug(cursor, bug_id, state_id)
        else:
            self._delete_for_bug(cursor, bug_id)

    def _get_id(self, cursor, value):
        cursor.execute("""
                SELECT id
                FROM %(value_table)s
                WHERE name = '%(value)s';
                """ % {"value_table":self.value_table, "value":value})
        ans = cursor.fetchone()
        if ans:
            return ans[0]
        else:
            return None
            
    def _delete_for_bug(self, cursor, bug_id):
        cursor.execute("""
                DELETE FROM %(table)s
                WHERE bug_id=%(bug_id)d;
                """ % {"table":self.bug_table, "bug_id":bug_id})

    def _update_for_bug(self, cursor, bug_id, state_id):
        cursor.execute("""
                UPDATE %(table)s
                SET id = %(state_id)d
                WHERE bug_id = %(bug_id)d;
                """ % {"table":self.bug_table,
                       "bug_id":bug_id,
                       "state_id":state_id})

    def _insert_for_bug(self, cursor, bug_id, state_id):
        cursor.execute("""
                INSERT INTO %(table)s (bug_id, id)
                VALUES (%(bug_id)d, %(state_id)d);
                """ % {"table":self.bug_table,
                       "bug_id":bug_id,
                       "state_id":state_id})


class Priorities(StateTable):

    valid_value = re.compile("^[a-zA-Z0-9.\(\) ]+$")
    bug_table = "priorities"
    value_table = "priority_values"
    alphabetical = False

    def __init__(self, connection):
        StateTable.__init__(self, connection)
        existing_values = self.values
        for value in ("1", "2", "3", "4", "5"):
            if value not in existing_values:
                logger.info("Adding (unchangeable) Priority value: %s" % \
                            value)
                self.create_new_value(value)


class Configurations(StateTable):

    valid_value = re.compile("^[a-zA-Z0-9. ]+$")
    bug_table = "configurations"
    value_table = "configuration_values"


class Categories(StateTable):

    valid_value = re.compile("^[a-zA-Z0-9. ]+$")
    bug_table = "categories"
    value_table = "category_values"


class Versions(StateTable):
    
    valid_value = re.compile("^[a-zA-Z0-9. \-_]+$")
    value_table = "versions"


class ReportedIns(Versions):

    bug_table = "reported_ins"


class FixedIns(Versions):

    bug_table = "fixed_ins"


class ClosedIns(Versions):

    bug_table = "closed_ins"


class Summary(object):

    def __init__(self, connection):
        self.connection = connection

    def _get_status_counts(self):
        cursor = self.connection.cursor()

        class Count:
            new = 0
            reviewed = 0
            scheduled = 0
            fixed = 0
            closed = 0
            cancelled = 0

        cursor.execute("""
                SELECT statuses.name,
                       COUNT(*)
                FROM statuses, bugs
                WHERE bugs.status_id = statuses.status_id
                GROUP BY statuses.name;
        """)
        result = cursor.fetchall()
        count = Count()
        for row in result:
            variable, value = row
            setattr(count, variable, value)
        cursor.close()
        return count

    status_counts = property(_get_status_counts)


class Bug(object):

    """A single bug cached from the database."""

    def __init__(self, bugs, bug_id):
        assert isinstance(bug_id, int)
        self.bugs = bugs
        self.bug_id = bug_id
        self.user_id = None
        self.date = None
        self.title = None
        self.status = None
        self.priority = None
        self.configuration = None
        self.category = None
        self.reported_in = None
        self.fixed_in = None
        self.closed_in = None
        self._read_bug_from_database()
        
    def _read_bug_from_database(self):
        cursor = self.bugs.connection.cursor()
        cursor.execute("""
                SELECT user_id,
                       date,
                       title,
                       statuses.name,
                       priority_values.name,
                       configuration_values.name,
                       category_values.name,
                       reported_versions.name,
                       fixed_versions.name,
                       closed_versions.name                       
                FROM (((((((((((((
                           statuses INNER JOIN bugs ON
                           (bugs.status_id = statuses.status_id)

                         ) LEFT OUTER JOIN priorities ON
                           (priorities.bug_id = %(bug_id)s)
                         ) LEFT OUTER JOIN priority_values ON
                           (priority_values.id = priorities.id)

                         ) LEFT OUTER JOIN configurations ON
                           (configurations.bug_id = %(bug_id)s)
                         ) LEFT OUTER JOIN configuration_values ON
                           (configuration_values.id = configurations.id)

                         ) LEFT OUTER JOIN categories ON
                           (categories.bug_id = %(bug_id)s)
                         ) LEFT OUTER JOIN category_values ON
                           (category_values.id = categories.id)

                         ) LEFT OUTER JOIN reported_ins ON
                           (reported_ins.bug_id = %(bug_id)s)
                         ) LEFT OUTER JOIN versions AS reported_versions ON
                           (reported_versions.id = reported_ins.id)

                         ) LEFT OUTER JOIN fixed_ins ON
                           (fixed_ins.bug_id = %(bug_id)s)
                         ) LEFT OUTER JOIN versions AS fixed_versions ON
                           (fixed_versions.id = fixed_ins.id)

                         ) LEFT OUTER JOIN closed_ins ON
                           (closed_ins.bug_id = %(bug_id)s)
                         ) LEFT OUTER JOIN versions AS closed_versions ON
                           (closed_versions.id = closed_ins.id))
                WHERE bugs.bug_id = %(bug_id)s;
                """ % {"bug_id": self.bug_id})
        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            (self.user_id,
             self.date,
             title,
             self.status,
             priority,
             configuration,
             category,
             # TODO keywords (?)
             reported_in,
             fixed_in,
             closed_in) = result
            # Convert None's into ""s
            self.priority = priority or ""
            self.configuration = configuration or ""
            self.category = category or ""
            # TODO keywords
            self.reported_in = reported_in or ""
            self.fixed_in = fixed_in or ""
            self.closed_in = closed_in or ""
            self.title = lib.unquote(title)
        else:
            raise NoSuchBugException, self.bug_id

    def _get_comments(self):
        return Comments(self.bugs.connection, self.bug_id)

    comments = property(_get_comments)

    def _get_status_hint(self):
        return getattr(StatusHints, self.status)

    status_hint = property(_get_status_hint)

    def change(self, user, cursor=None, **args):
        own_cursor = False
        if not cursor:
            cursor = self.bugs.connection.cursor()
            own_cursor = True
        try:
            try:
                if "status" in args:
                    status = args.pop("status")
                    self.bugs.statuses.set_for_bug(
                        cursor, self.bug_id, status)
                if "priority" in args:
                    priority = args.pop("priority")
                    self.bugs.priorities.set_for_bug(
                        cursor, self.bug_id, priority)
                if "configuration" in args:
                    configuration = args.pop("configuration")
                    self.bugs.configurations.set_for_bug(
                        cursor, self.bug_id, configuration)
                if "category" in args:
                    category = args.pop("category")
                    self.bugs.categories.set_for_bug(
                        cursor, self.bug_id, category)
                # TODO keywords
                if "reported_in" in args:
                    reported_in = args.pop("reported_in")
                    self.bugs.reported_ins.set_for_bug(
                        cursor, self.bug_id, reported_in)
                if "fixed_in" in args:
                    fixed_in = args.pop("fixed_in")
                    self.bugs.fixed_ins.set_for_bug(
                        cursor, self.bug_id, fixed_in)
                if "closed_in" in args:
                    closed_in = args.pop("closed_in")
                    self.bugs.closed_ins.set_for_bug(
                        cursor, self.bug_id, closed_in)
                if "comment" in args:
                    comment = args.pop("comment")
                    if "timestamp" in args:
                        timestamp = args.pop("timestamp")
                        self.comments.add(cursor, user, comment, timestamp)
                    else:
                        self.comments.add(cursor, user, comment)
                if args:
                    raise TypeError, "excess keyword arguments: %s" % args
                self.bugs.connection.commit()
            except:
                self.bugs.connection.rollback()
                raise
        finally:
            if own_cursor:
                cursor.close()


class Row:

    """The super class off all Row objects returned from Bugs."""

    # All defined by the subclass.
    status = None
    titles = None
    variables = None
    sorted_by = None
    ordered = None
    
    def __init__(self, bug_id, priority,  category,
                 reported_in, fixed_in, closed_in, title):
        self.bug_id = bug_id
        self.priority = priority or ""
        self.category = category or ""
        self.reported_in = reported_in or ""
        self.fixed_in = fixed_in or ""
        self.closed_in = closed_in or ""
        self.title = lib.unquote(title)
    
    def get(self):
        return [(variable, getattr(self, variable))
                for variable in self.variables]

    def __len__(self):
        return len(self.titles)

        
class Bugs(object):

    def __init__(self, connection):
        self.connection = connection
        self.statuses = Statuses(connection)
        self.priorities = Priorities(connection)
        self.configurations = Configurations(connection)
        self.categories = Categories(connection)
        self.reported_ins = ReportedIns(connection)
        self.fixed_ins = FixedIns(connection)
        self.closed_ins = ClosedIns(connection)
        self.summary = Summary(connection)

    def purge(self):
        self.configurations.purge()
        self.categories.purge()
        self.reported_ins.purge()
        self.fixed_ins.purge()
        self.closed_ins.purge()
        
    def _add_to_bugs_table(self, cursor, user, title):
        title = lib.quote(title)
        cursor.execute("""
                INSERT INTO bugs (user_id, date, title, status_id)
                       VALUES (%d, 'now', '%s', %d);
                """ % (user.user_id, title, self.statuses.initial_id))
        cursor.execute("SELECT currval('bug_ids_seq')")
        bug_id = cursor.fetchone()[0]
        return bug_id

    def _import_into_bugs_table(self, cursor, user, timestamp, bug_id, title):
        title = lib.quote(title)
        cursor.execute("""
                INSERT INTO bugs (bug_id, user_id, date, title, status_id)
                       VALUES (%d, %d, '%s', '%s', %d);
                """ % (int(bug_id), user.user_id, timestamp, title,
                       self.statuses.initial_id))
        cursor.execute("""
                SELECT setval('bug_ids_seq', (SELECT MAX(bug_id) FROM bugs));
        """)

    def add(self, user, title=None, version=None, configuration=None,
            category=None, description=None):
        cursor = self.connection.cursor()
        bug_id = self._add_to_bugs_table(cursor, user, title)
        changes = {}
        if version:
            changes["reported_in"] = version
        if configuration:
            changes["configuration"] = configuration
        if category:
            changes["category"] = category
        if description:
            changes["comment"] = description
        if changes:
            bug = self.get(bug_id)
            bug.change(user, cursor, **changes)
        self.connection.commit()
        cursor.close()
        return bug_id

    def import_bug(self, user, timestamp, bug_id, title, status, category,
                   configuration, reported_in, fixed_in, closed_in):
        cursor = self.connection.cursor()
        self._import_into_bugs_table(cursor, user, timestamp, bug_id, title)
        bug = self.get(bug_id)
        changes = {"status": status,
                   "category": category,
                   "configuration": configuration,
                   "reported_in": reported_in,
                   "fixed_in": fixed_in,
                   "closed_in": closed_in}
        bug.change(user, cursor, **changes)
        self.connection.commit()
        cursor.close()
    
    def get(self, bug_id):
        try:
            bug_id = int(bug_id)
        except ValueError:
            raise NoSuchBugException, bug_id
        return Bug(self, bug_id)

    def _get_list(self, row_cls):
        sort_by_map = {
            "bug_id": "bugs.bug_id",
            "priority": "priority_values.name",
            "category": "category_values.name",
            "reported_in": "reported_versions.name",
            "fixed_in": "fixed_versions.name",
            "closed_in": "closed_versions.name",
            "title": "title"}
        order_map = {
            "ascending": "ASC",
            "descending": "DESC"}

        assert row_cls.sorted_by in row_cls.variables
        assert row_cls.sorted_by in sort_by_map
        assert row_cls.ordered in order_map
    
        cursor = self.connection.cursor()
        cursor.execute("""
                SELECT bugs.bug_id,
                       priority_values.name,
                       category_values.name,
                       reported_versions.name,
                       fixed_versions.name,
                       closed_versions.name,
                       title
                FROM ((((((((((
                           statuses INNER JOIN bugs ON
                           (bugs.status_id = statuses.status_id)

                         ) LEFT OUTER JOIN priorities ON
                           (priorities.bug_id = bugs.bug_id
                         ) LEFT OUTER JOIN priority_values ON
                           (priority_values.id = priorities.id)
                           
                         ) LEFT OUTER JOIN categories ON
                           (categories.bug_id = bugs.bug_id)
                         ) LEFT OUTER JOIN category_values ON
                           (category_values.id = categories.id)
                           
                         ) LEFT OUTER JOIN reported_ins ON
                           (reported_ins.bug_id = bugs.bug_id)
                         ) LEFT OUTER JOIN versions AS reported_versions ON
                           (reported_versions.id = reported_ins.id)

                         ) LEFT OUTER JOIN fixed_ins ON
                           (fixed_ins.bug_id = bugs.bug_id)
                         ) LEFT OUTER JOIN versions AS fixed_versions ON
                           (fixed_versions.id = fixed_ins.id)

                         ) LEFT OUTER JOIN closed_ins ON
                           (closed_ins.bug_id = bugs.bug_id)
                         ) LEFT OUTER JOIN versions AS closed_versions ON
                           (closed_versions.id = closed_ins.id))
                WHERE statuses.name = '%(status)s'
                ORDER BY %(sort_by)s %(order)s;
                """ % {"status": row_cls.status,
                       "sort_by": sort_by_map[row_cls.sorted_by],
                       "order": order_map[row_cls.ordered]})
        rows = []
        result = cursor.fetchall()
        for row in result:
            rows.append(row_cls(*row))
        cursor.close()
        return rows

    def get_list(self, status, *args):
        return getattr(self, "get_%s_list" % status)(*args)

    def get_new_list(self, sort_by, order):
        if not sort_by:
            sort_by = "category"
        if not order:
            order = "ascending"

        class NewRow(Row):

            status = "new"
            titles = "Bug", "Category", "Reported in", "Title"
            variables = "bug_id", "category", "reported_in", "title"
            sorted_by = sort_by
            ordered = order
        
        return self._get_list(NewRow)

    def get_reviewed_list(self, sort_by, order):
        if not sort_by:
            sort_by = "priority"
        if not order:
            order = "descending"

        class ReviewedRow(Row):

            status = "reviewed"
            titles = "Bug", "Priority", "Category", "Reported in", "Title"
            variables = ("bug_id", "priority", "category",
                         "reported_in", "title")
            sorted_by = sort_by
            ordered = order

        return self._get_list(ReviewedRow)
            
    def get_scheduled_list(self, sort_by, order):
        if not sort_by:
            sort_by = "priority"
        if not order:
            order = "descending"

        class ScheduledRow(Row):

            status = "scheduled"
            titles = "Bug", "Priority", "Category", "Reported in", "Title"
            variables = ("bug_id", "priority", "category",
                         "reported_in", "title")
            sorted_by = sort_by
            ordered = order

        return self._get_list(ScheduledRow)
            
    def get_fixed_list(self, sort_by, order):
        if not sort_by:
            sort_by = "fixed_in"
        if not order:
            order = "ascending"

        class FixedRow(Row):

            status = "fixed"
            titles = "Bug", "Priority", "Category", "Fixed in", "Title"
            variables = ("bug_id", "priority", "category",
                         "fixed_in", "title")
            sorted_by = sort_by
            ordered = order

        return self._get_list(FixedRow)
            
    def get_closed_list(self, sort_by, order):
        if not sort_by:
            sort_by = "closed_in"
        if not order:
            order = "ascending"

        class ClosedRow(Row):

            status = "closed"
            titles = "Bug", "Priority", "Category", "Closed in", "Title"
            variables = ("bug_id", "priority", "category",
                         "closed_in", "title")
            sorted_by = sort_by
            ordered = order

        return self._get_list(ClosedRow)
            
    def get_cancelled_list(self, sort_by, order):
        if not sort_by:
            sort_by = "bug_id"
        if not order:
            order = "ascending"

        class CancelledRow(Row):

            status = "cancelled"
            titles = "Bug", "Title"
            variables = "bug_id", "title"
            sorted_by = sort_by
            ordered = order

        return self._get_list(CancelledRow)
            

class Application(object):

    def __init__(self, connection):
        self.users = Users(connection)
        self.bugs = Bugs(connection)
        
    def new_session(self, session_id):
        pass

    def expired_session(self, session_id):
        self.users.expired_session(session_id)
            
    def create_new_user(self, username, name, email, password):
        return self.users.create_new_user(username, name, email, password)

    def _get_usernames(self):
        return self.users.usernames

    usernames = property(_get_usernames)

    def email_password(self, username):
        return self.users.email_password(username)
        
    def login(self, session_id, username, password):
        return self.users.login(session_id, username, password)

    def logout(self, session_id):
        return self.users.logout(session_id)

    def get_user(self, session_id):
        return self.users.get_user(session_id)

    def add_bug(self, session_id, **args):
        user = self.users.get_user(session_id)
        if user is not None:
            return self.bugs.add(user, **args)
        return None

    def _if_have_user(self, session_id, f, *args):
        if self.users.get_user(session_id):
            return f(*args)
        else:
            return None

    def get_bug(self, session_id, bug_id):
        if self.users.get_user(session_id):
            return self.bugs.get(bug_id)
        else:
            return None

    def get_bugs(self, session_id, status, sort_by, order):
        if self.users.get_user(session_id):
            return self.bugs.get_list(status, sort_by, order)
        else:
            return None

    def get_status_counts(self, session_id):
        if self.users.get_user(session_id):
            return self.bugs.summary.status_counts
        else:
            return None

    def _get_statuses(self):
        return self.bugs.statuses.values

    statuses = property(_get_statuses)

    def _get_priorities(self):
        return self.bugs.priorities.values

    priorities = property(_get_priorities)

    def _get_configurations(self):
        return self.bugs.configurations.values

    configurations = property(_get_configurations)

    def _get_categories(self):
        return self.bugs.categories.values

    categories = property(_get_categories)

    def _get_versions(self):
        return self.bugs.reported_ins.values

    versions = property(_get_versions)

    # TODO keywords

    def purge(self):
        self.bugs.purge()
