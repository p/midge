"""Export BugTracker bugs ready for import into PyBug.

Do not include any intermediate IDs in this intermediate format.

Note that although we connect to a live database, we never commit, so
we cannot change anything.

"""

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
                    scheduled_id int,
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
                    scheduled_id,
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
                    to_be_closed_in_version_id,
                    database_id,
                    priority,
                    description,
                    created_by,
                    created_date
            FROM phpbt_bug
    """)

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

def create_scheduled_t_from_version_t(cursor):
    cursor.execute("""
    CREATE TEMPORARY TABLE scheduled_t (scheduled_id int, scheduled_name text)
    """)
    cursor.execute("""
    INSERT INTO scheduled_t (scheduled_id, scheduled_name)
            SELECT version_id, version_name
            FROM version_t
    """)

def remove_roundup_bugs(cursor):
    cursor.execute("""
    DELETE FROM bug_t WHERE status_id=2
    """)

def map_status_values(cursor):
    cursor.execute("""
    UPDATE status_t
            SET status_name='New'
            WHERE status_name='Reopened'
    """)
    cursor.execute("""
    UPDATE status_t
            SET status_name='Closed'
            WHERE status_name='Verified'
    """)
    cursor.execute("""
    UPDATE status_t
            SET status_name='Fixed'
            WHERE status_name='Resolved'
    """)
    cursor.execute("""
    UPDATE status_t
            SET status_name='Reviewed'
            WHERE status_name='Assigned'
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

def map_scheduled_values(cursor):
    cursor.execute("""
    UPDATE scheduled_t
            SET scheduled_name='Yes'
            WHERE scheduled_name NOT IN ('Soon', 'Distant')
    """)
    cursor.execute("""
    UPDATE scheduled_t
            SET scheduled_name='No'
            WHERE scheduled_name IN ('Soon', 'Distant')
    """)



def get_bugs(cursor):
    cursor.execute("""
    SELECT
            bug_id AS id,
            status_name AS status,
            category_name AS category,
            v1.version_name AS reported_in,
            v2.version_name AS fixed_in,
            v3.version_name AS closed_in,
            scheduled_name AS scheduled,
            database_name AS configuration,
            priority
            FROM
                    bug_t,
                    status_t,
                    category_t,
                    version_t v1,
                    version_t v2,
                    version_t v3,
                    scheduled_t,
                    phpbt_database_server
            WHERE bug_t.status_id = status_t.status_id
                    AND bug_t.category_id = category_t.category_id
                    AND bug_t.reported_in_id = v1.version_id
                    AND bug_t.fixed_in_id = v2.version_id
                    AND bug_t.closed_in_id = v3.version_id
                    AND bug_t.scheduled_id = scheduled_t.scheduled_id
                    AND bug_t.configuration_id = phpbt_database_server.database_id
    """)
    return cursor.fetchall()


def get_comments(cursor):
    comments = []
    cursor.execute("""
        SELECT
                bug_id,
                login,
                bug_t.created_date,
                description
        FROM
                bug_t,
                phpbt_auth_user
        WHERE
                phpbt_auth_user.user_id = bug_t.created_by
    """)
    comments += cursor.fetchall()
    cursor.execute("""
        SELECT
                bug_id,
                login,
                phpbt_comment.created_date,
                comment_text
        FROM
                phpbt_comment,
                phpbt_auth_user
        WHERE
                phpbt_auth_user.user_id = phpbt_comment.created_by
    """)
    comments += cursor.fetchall()
    return comments



import MySQLdb
database = MySQLdb.connect(user="phpbt", passwd="iiw6ieVe", db="phpbt")
cursor = database.cursor()

create_bug_t_from_phpbt_bug(cursor)
create_status_t_from_phpbt_status(cursor)
create_category_t_from_phpbt_component(cursor)
create_version_t_from_phpbt_version(cursor)
# TODO create database_id also with a '0' entry to empty string.
create_scheduled_t_from_version_t(cursor)
remove_roundup_bugs(cursor)
map_status_values(cursor)
map_category_values(cursor)
map_scheduled_values(cursor)

bugs = get_bugs(cursor)
comments = get_comments(cursor)

bugs_d = {}
for bug in bugs:
    bugs_d[int(bug[0])] = bug

print bugs_d.keys()

for comment in comments:
    if int(comment[0]) not in bugs_d:
        print "Found comment without bug: %d" % comment[0]

# bugs_f = file("bugs.txt", "w")
# print "Writing bugs into 'bugs.txt'"
# bugs_f.write(repr(bugs))
# bugs_f.close

# comments_f = file("comments.txt", "w")
# print "Writing comments into 'comments.txt'"
# comments_f.write(repr(comments))
# comments_f.close()
# print "Done"

cursor.execute("DROP TABLE version_t")

#database.rollback()
