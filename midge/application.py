# $Id$
# (C) Timothy Corbett-Clark, 2004

"""The main bugtracking application with concepts of users, bugs, etc."""

import re
import sets
import textwrap

import midge.connection as connection
import midge.lib as lib
import midge.logger as logger


def quote(x):
    # TODO make more efficient - use translate?
    x = x.replace("\b", r"\b")
    x = x.replace("\f", r"\f")
    x = x.replace("\r", r"\r")
    x = x.replace("\n", r"\n")
    x = x.replace("\t", r"\t")
    x = x.replace("'", r"\047")
    return x


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
        username = quote(username)
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
        password = quote(password)
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
            return self._get_attribute("password")
        return None

    def set_password(self, password):
        if self.user_id is not None:
            password = quote(password)
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
            value = ans[0]
        cursor.close()
        return value

    def _set_attribute(self, attribute, value):
        assert self.user_id
        value = quote(value)
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
        username = quote(username)
        name = quote(name)
        email = quote(email)
        password = quote(password)
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
                SELECT username FROM users ORDER BY username;
                """)
        usernames = [row[0] for row in cursor.fetchall()]
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
                self.append(Comment(self.bug_id,
                                    users_name,
                                    username,
                                    date,
                                    text))
        else:
            raise UnableToReadCommentsException, self.bug_id

    def add(self, cursor, user, text, timestamp="now"):
        text = quote(text.strip())
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
            raise InvalidValueException, (bug_id, status)


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
        # TODO

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
        value = str(value).strip()
        if value:
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

    valid_value = re.compile(r"^[a-zA-Z0-9. _/()-]+$")
    bug_table = "configurations"
    value_table = "configuration_values"


class Categories(StateTable):

    valid_value = re.compile(r"^[a-zA-Z0-9. _/-]+$")
    bug_table = "categories"
    value_table = "category_values"


class Keywords(StateTable):

    valid_value = re.compile(r"^[a-zA-Z0-9. _/-]+$")
    bug_table = "keywords"
    value_table = "keyword_values"


class Versions(StateTable):
    
    valid_value = re.compile(r"^[a-zA-Z0-9. _/-]+$")
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
        self.keyword = None
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
                       keyword_values.name,
                       reported_versions.name,
                       fixed_versions.name,
                       closed_versions.name                       
                FROM (((((((((((((((
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

                         ) LEFT OUTER JOIN keywords ON
                           (keywords.bug_id = %(bug_id)s)
                         ) LEFT OUTER JOIN keyword_values ON
                           (keyword_values.id = keywords.id)

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
             keyword,
             reported_in,
             fixed_in,
             closed_in) = result
            # Convert None's into ""s
            self.priority = priority or ""
            self.configuration = configuration or ""
            self.category = category or ""
            self.keyword = keyword or ""
            self.reported_in = reported_in or ""
            self.fixed_in = fixed_in or ""
            self.closed_in = closed_in or ""
            self.title = title
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
                if "keyword" in args:
                    keyword = args.pop("keyword")
                    self.bugs.keywords.set_for_bug(
                        cursor, self.bug_id, keyword)
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


class Search:

    _all = (("bug_id", "Bug"),
            ("status", "Status"),
            ("priority", "Priority"),
            ("category", "Category"),
            ("configuration", "Configuration"),
            ("keyword", "Keyword"),
            ("reported_in", "Reported in"),
            ("fixed_in", "Fixed in"),
            ("closed_in", "Closed in"),
            ("title", "Title"))

    _order_map = dict(
        ascending = "ASC",
        descending = "DESC")

    _select_map = dict(
        bug_id = "bugs.bug_id",
        status = "statuses.name",
        priority = "priority_values.name",
        category = "category_values.name",
        configuration = "configuration_values.name",
        keyword = "keyword_values.name",
        reported_in = "reported_versions.name",
        fixed_in = "fixed_versions.name",
        closed_in = "closed_versions.name",
        title = "title")

    _from_map = dict(
        priority = """
               ) LEFT OUTER JOIN priorities ON
                (priorities.bug_id = bugs.bug_id)
               ) LEFT OUTER JOIN priority_values ON
                (priority_values.id = priorities.id)""",
        category = """
               ) LEFT OUTER JOIN categories ON
                (categories.bug_id = bugs.bug_id)
               ) LEFT OUTER JOIN category_values ON
                (category_values.id = categories.id)""",
        configuration = """
               ) LEFT OUTER JOIN configurations ON
                (configurations.bug_id = bugs.bug_id)
               ) LEFT OUTER JOIN configuration_values ON
                (configuration_values.id = configurations.id)""",
        keyword = """
               ) LEFT OUTER JOIN keywords ON
                (keywords.bug_id = bugs.bug_id)
               ) LEFT OUTER JOIN keyword_values ON
                (keyword_values.id = keywords.id)""",
        reported_in = """
               ) LEFT OUTER JOIN reported_ins ON
                (reported_ins.bug_id = bugs.bug_id)
               ) LEFT OUTER JOIN versions AS reported_versions ON
                (reported_versions.id = reported_ins.id)""",
        fixed_in = """
               ) LEFT OUTER JOIN fixed_ins ON
                (fixed_ins.bug_id = bugs.bug_id)
               ) LEFT OUTER JOIN versions AS fixed_versions ON
                (fixed_versions.id = fixed_ins.id)""",
        closed_in = """
               ) LEFT OUTER JOIN closed_ins ON
                (closed_ins.bug_id = bugs.bug_id)
               ) LEFT OUTER JOIN versions AS closed_versions ON
                (closed_versions.id = closed_ins.id)""")

    _where_map = {
        "status": "statuses.name = '%s'",
        "status_regex": "statuses.name ~* '%s'",
        "priority": "priority_values.name = '%s'",
        "priority_regex": "priority_values.name ~* '%s'",
        "category": "category_values.name = '%s'",
        "category_regex": "category_values.name ~* '%s'",
        "configuration": "configuration_values.name = '%s'",
        "configuration_regex": "configuration_values.name ~* '%s'",
        "keyword": "keyword_values.name = '%s'",
        "keyword_regex": "keyword_values.name ~* '%s'",
        "reported_in": "reported_versions.name = '%s'",
        "reported_in_regex": "reported_versions.name ~* '%s'",
        "fixed_in": "fixed_versions.name = '%s'",
        "fixed_in_regex": "fixed_versions.name ~* '%s'",
        "closed_in": "closed_versions.name = '%s'",
        "closed_in_regex": "closed_versions.name ~* '%s'",
        "title": "title ~* '%s'",
        }

    def __init__(self, variables, sort_by, order, **criteria):
        """Construct an object defining a search.

        The order of the columns is fixed, but which columns are
        included is provided by the variables parameter.

        sort_by and order determine by which column the results are
        sorted and in which order.

        The subset of the data is provided by the **criteria
        argument. E.g.
           status="new"
           keyword_regex="comms|replication"

        For example, a search used to list all the new bugs could be
        defined:

           Search(("bug_id", "category", "reported_in", "title"),
                  "category", "ascending", status="new")

        """
        self.variables, self.titles = self._make_variables_and_titles(variables)
        self.sort_by = sort_by
        self.order = order
        self.criteria = criteria
        self.rows = []

        assert self.sort_by in self.variables
        assert self.order in ("ascending", "descending")
        assert type(self.criteria) == type({})

    def _make_variables_and_titles(self, variables):
        variables_set = sets.Set(variables)
        variables = []
        titles = []
        for v, t in self._all:
            if v in variables_set:
                variables.append(v)
                titles.append(t)
                variables_set.remove(v)
        assert len(variables_set) == 0
        return tuple(variables), tuple(titles)

    def _make_select_clause(self, variables):
        return "SELECT " + ", ".join([self._select_map[v] for v in variables])

    def _make_from_clause(self, variables, criteria):
        v_set = sets.Set(variables)
        for v in criteria:
            if v.endswith("_regex"):
                v = v[:-len("_regex")]
            v_set.add(v)
        clauses = filter(None, [self._from_map.get(v, None) for v in v_set])
        return """FROM %(from_brackets)s
                  statuses INNER JOIN bugs ON
                  (bugs.status_id = statuses.status_id)
                  %(from)s""" % {"from_brackets": len(clauses) * "((",
                                 "from": " ".join(clauses)}

    def _make_where_clause(self, criteria):
        for key in criteria:
            criteria[key] = quote(criteria[key])
        clauses = [self._where_map[c] % v for c,v in criteria.iteritems()]
        if clauses:
            return "WHERE " + " AND ".join(clauses)
        else:
            return ""

    def _make_sort_clause(self, sort_by, order):
        return "ORDER BY %s %s" % (self._select_map[sort_by],
                                  self._order_map[order])
    
    def run(self, cursor):
        # TODO try except to ensure cursor is closed after error.
        search_sql = """
               %(select)s
               %(from)s
               %(where)s
               %(sort)s;""" % {
            "select": self._make_select_clause(self.variables),
            "from": self._make_from_clause(self.variables, self.criteria),
            "where": self._make_where_clause(self.criteria),
            "sort": self._make_sort_clause(self.sort_by, self.order)}
        cursor.execute(search_sql)
        self.rows = []
        result = cursor.fetchall()
        for row in result:
            self.add(*row)
        cursor.close()

    def add(self, *args):
        assert len(args) == len(self.variables)
        self.rows.append(Row(self.variables, *args))

   
class Row:

    """A Search has a list of Rows."""

    def __init__(self, variable_names, *args):
        """Initialise a row forming part of a Search.

        Only to be called from within the Search class.

        Once constructed, the values are accessed as attributes or
        using the get method.

        """
        self.variable_names = variable_names
        assert len(args) == len(self.variable_names)
        for variable, value in zip(self.variable_names, args):
            setattr(self, variable, value or "")
    
    def get(self):
        """Return a list of all values in correct order."""
        return [(variable, getattr(self, variable))
                for variable in self.variable_names]

    def __len__(self):
        return len(self.variable_names)

        
class Bugs(object):

    def __init__(self, connection):
        self.connection = connection
        self.statuses = Statuses(connection)
        self.priorities = Priorities(connection)
        self.configurations = Configurations(connection)
        self.categories = Categories(connection)
        self.keywords = Keywords(connection)
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
        title = quote(title)
        cursor.execute("""
                INSERT INTO bugs (user_id, date, title, status_id)
                       VALUES (%d, 'now', '%s', %d);
                """ % (user.user_id, title, self.statuses.initial_id))
        cursor.execute("SELECT currval('bug_ids_seq')")
        bug_id = cursor.fetchone()[0]
        return bug_id

    def _import_into_bugs_table(self, cursor, user, timestamp, bug_id, title):
        title = quote(title)
        cursor.execute("""
                INSERT INTO bugs (bug_id, user_id, date, title, status_id)
                       VALUES (%d, %d, '%s', '%s', %d);
                """ % (int(bug_id), user.user_id, timestamp, title,
                       self.statuses.initial_id))
        cursor.execute("""
                SELECT setval('bug_ids_seq', (SELECT MAX(bug_id) FROM bugs));
        """)

    def add(self, user, title=None, version=None, configuration=None,
            category=None, keyword=None, description=None):
        cursor = self.connection.cursor()
        bug_id = self._add_to_bugs_table(cursor, user, title)
        changes = {}
        if version:
            changes["reported_in"] = version
        if configuration:
            changes["configuration"] = configuration
        if category:
            changes["category"] = category
        if keyword:
            changes["keyword"] = keyword
        if description:
            changes["comment"] = description
        if changes:
            bug = self.get(bug_id)
            bug.change(user, cursor, **changes)
        self.connection.commit()
        cursor.close()
        return bug_id

    def import_bug(self, bug_id, user, timestamp, title, status, priority,
                   category, configuration, keyword,
                   reported_in, fixed_in, closed_in):
        cursor = self.connection.cursor()
        self._import_into_bugs_table(cursor, user, timestamp, bug_id, title)
        bug = self.get(bug_id)
        changes = {"status": status,
                   "priority": priority,
                   "category": category,
                   "configuration": configuration,
                   "keyword": keyword,
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

    def search(self, search):
        search.run(self.connection.cursor())

           
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

    def search(self, session_id, search):
        if self.users.get_user(session_id):
            return self.bugs.search(search)
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

    def _get_keywords(self):
        return self.bugs.keywords.values

    keywords = property(_get_keywords)

    def purge(self):
        self.bugs.purge()

