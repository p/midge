# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Example functionality to extract bugs from phpBugTracker.

Create 3 files ready for import into Midge using midge.io.

Note that although we connect to a live database, we never commit, so
we cannot change anything.

"""


import MySQLdb
import time


def cleanup(cursor):
    for table in "version_t", "database_t", "users_t":
        try:
            cursor.execute("DROP TABLE %s" % table)
        except:
            pass

def create_bug_t_from_phpbt_bug(cursor):
    cursor.execute("""
    CREATE TEMPORARY TABLE
            bug_t (
                    bug_id int,
                    title text,
                    status_id int,
                    category_id int,
                    reported_in_id int,
                    fixed_in_id int,
                    closed_in_id int,
                    configuration_id int,
                    priority int,
                    description text,
                    created_by int,
                    created_date bigint
            )""")
    cursor.execute("""
    INSERT INTO 
            bug_t (
                    bug_id,
                    title,
                    status_id,
                    category_id,
                    reported_in_id,
                    fixed_in_id,
                    closed_in_id,
                    configuration_id,
                    priority,
                    description,
                    created_by,
                    created_date
            )
            SELECT
                    bug_id,
                    title,
                    status_id,
                    component_id,
                    version_id,
                    closed_in_version_id,
                    closed_in_version_id,
                    database_id,
                    priority,
                    description,
                    created_by,
                    created_date
            FROM phpbt_bug
    """)

def create_users_t_from_phpbt_auth_user(cursor):
    cursor.execute("""
    CREATE TEMPORARY TABLE users_t
          (user_id INT,
           user_name TEXT,
           name TEXT,
           email TEXT)
    """)

    cursor.execute("""
    SELECT user_id, login, first_name, last_name, email
    FROM phpbt_auth_user
    """)
    
    users = []
    users.append( (0, "retired", "retired", "tcorbettclark@cmedltd.com") )
    for user_id, username, firstname, lastname, email in cursor.fetchall():
        if "@" in username:
            username = username.split("@")[0]
        if username.startswith("developers"):
            users.append( (user_id, "retired", "retired",
                           "tcorbettclark@cmedltd.com") )
        else:
            users.append( (user_id, username,
                           "%s %s" % (firstname, lastname), email) )

    for user_id, username, name, email in users:
        cursor.execute("""
        INSERT INTO users_t VALUES (%d, '%s', '%s', '%s')
        """ % (user_id, username, name, email))

    
def create_status_t_from_phpbt_status(cursor):
    cursor.execute("""
    CREATE TEMPORARY TABLE status_t (status_id int, status_name text)
    """)
    cursor.execute("""
    INSERT INTO status_t (status_id, status_name)
            SELECT status_id, status_name 
            FROM phpbt_status
    """)

def create_category_t_from_phpbt_component(cursor):
    cursor.execute("""
    CREATE TEMPORARY TABLE category_t (category_id int, category_name text)
    """)
    cursor.execute("""
    INSERT INTO category_t (category_id, category_name)
            SELECT component_id, component_name
            FROM phpbt_component
    """)

def create_version_t_from_phpbt_version(cursor):
    cursor.execute("""
    CREATE TABLE version_t (version_id int, version_name text)
    """)
    cursor.execute("""
    INSERT INTO version_t (version_id, version_name)
                SELECT version_id, version_name
                FROM phpbt_version
    """)
    cursor.execute("""
    INSERT INTO version_t (version_id, version_name)
    VALUES (0, "")
    """)

def create_database_t_from_phpbt_database_server(cursor):
    cursor.execute("""
    CREATE TABLE database_t (database_id INT, database_name TEXT)
    """)
    cursor.execute("""
    INSERT INTO database_t (database_id, database_name)
                SELECT database_id, database_name
                FROM phpbt_database_server
    """)
    cursor.execute("""
    INSERT INTO database_t (database_id, database_name)
    VALUES (0, "")
    """)

def remove_roundup_bugs(cursor):
    cursor.execute("""
    DELETE FROM bug_t WHERE status_id=2
    """)

def map_status_values(cursor):
    cursor.execute("""
    UPDATE status_t
            SET status_name='new'
            WHERE status_name='New'
    """)
    cursor.execute("""
    UPDATE status_t
            SET status_name='new'
            WHERE status_name='Reopened'
    """)
    cursor.execute("""
    UPDATE status_t
            SET status_name='closed'
            WHERE status_name='Closed'
    """)
    cursor.execute("""
    UPDATE status_t
            SET status_name='closed'
            WHERE status_name='Verified'
    """)
    cursor.execute("""
    UPDATE status_t
            SET status_name='fixed'
            WHERE status_name='Resolved'
    """)
    cursor.execute("""
    UPDATE status_t
            SET status_name='reviewed'
            WHERE status_name='Assigned'
    """)
    cursor.execute("""
    UPDATE status_t
            SET status_name='reviewed'
            WHERE status_name='Reviewed'
    """)

def map_category_values(cursor):
    cursor.execute("""
    UPDATE category_t
            SET category_name='Not Sure'
            WHERE category_name='Aaah - Not Sure'
    """)
    cursor.execute("""
    UPDATE category_t
            SET category_name='Not Sure'
            WHERE category_name='Old Roundup Bug'
    """)

def get_users(cursor):
    cursor.execute("""
    SELECT
            user_name,
            name,
            email
    FROM
            users_t
    """)
    users = {}
    for username, name, email in cursor.fetchall():
        if username not in users:
            users[username] = (username, name, email)
    return users.values()

def get_bugs(cursor):
    cursor.execute("""
    SELECT
            bug_id AS id,
            users_t.user_name,
            bug_t.created_date,
            bug_t.title,
            status_name AS status,
            priority,
            category_name AS category,
            database_name AS configuration,
            v1.version_name AS reported_in,
            v2.version_name AS fixed_in,
            v3.version_name AS closed_in
    FROM
            bug_t,
            status_t,
            category_t,
            version_t v1,
            version_t v2,
            version_t v3,
            database_t,
            users_t
    WHERE bug_t.status_id = status_t.status_id
      AND bug_t.category_id = category_t.category_id
      AND bug_t.reported_in_id = v1.version_id
      AND bug_t.fixed_in_id = v2.version_id
      AND bug_t.closed_in_id = v3.version_id
      AND bug_t.configuration_id = database_t.database_id
      AND users_t.user_id = bug_t.created_by
    """)
    bugs = []
    for bug in cursor.fetchall():
        bug = list(bug)
        bug[2] = time.ctime(bug[2])
        bugs.append(bug)
    return bugs

def get_comments(cursor):
    comments = []
    cursor.execute("""
        SELECT
                bug_id,
                user_name,
                bug_t.created_date,
                description
        FROM
                bug_t,
                users_t
        WHERE
                users_t.user_id = bug_t.created_by
    """)
    comments += cursor.fetchall()
    cursor.execute("""
        SELECT
                bug_id,
                user_name,
                phpbt_comment.created_date,
                comment_text
        FROM
                phpbt_comment,
                users_t
        WHERE
                users_t.user_id = phpbt_comment.created_by
    """)
    comments += cursor.fetchall()
    return [(bug_id, username,
             time.ctime(timestamp), description)
            for bug_id, username, timestamp, description in comments]


database = MySQLdb.connect(user="phpbt", passwd="iiw6ieVe", db="phpbt")
cursor = database.cursor()
cleanup(cursor)
create_bug_t_from_phpbt_bug(cursor)
create_users_t_from_phpbt_auth_user(cursor)
create_status_t_from_phpbt_status(cursor)
create_category_t_from_phpbt_component(cursor)
create_version_t_from_phpbt_version(cursor)
create_database_t_from_phpbt_database_server(cursor)
remove_roundup_bugs(cursor)
map_status_values(cursor)
map_category_values(cursor)

users = get_users(cursor)
bugs = get_bugs(cursor)
comments = get_comments(cursor)
print "Found %d users" % len(users)
print "Found %d bugs" % len(bugs)
print "Found %d comments" % len(comments)

cleanup(cursor)

bugs_d = {}
for bug in bugs:
    bugs_d[int(bug[0])] = bug

comments_without_bugs = []
for comment in comments:
    if int(comment[0]) not in bugs_d:
        comments_without_bugs.append(comment[0])
if comments_without_bugs:
    print "Comments without bugs: %s" % str(comments_without_bugs)

users_f = file("users.txt", "w")
print "Writing users into 'users.txt'"
users_f.write(repr(users))
users_f.close()

bugs_f = file("bugs.txt", "w")
print "Writing bugs into 'bugs.txt'"
bugs_f.write(repr(bugs))
bugs_f.close

comments_f = file("comments.txt", "w")
print "Writing comments into 'comments.txt'"
comments_f.write(repr(comments))
comments_f.close()
print "Done"


#database.rollback()
