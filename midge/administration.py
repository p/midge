# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Database adminstration functions for creating and destroying tables.

All these functions access the database without using the abstracted
connections found in connection.py.

Each bug has current state made up of many state variables e.g.
priority, reported in version, etc.
      
Unlike comments, states *are* changed. If a bug does not have a
corresponding state then the state table simply lacks a corresponding
entry. There are no defaults, and no NULLs.  Thus new states can be
added and changed during the lifetime of the tracking system.

Note that the value_table may be shared amongst different states.

"""

import psycopg

import midge.lib as lib
import midge.logger as logger
import midge.config as config


def run_sql(database, sql_commands):
    assert database in (config.Database.name, config.Database.test_name)
    connection = psycopg.connect(
        "dbname=%s user=%s password=%s" % (database,
                                           config.Database.user,
                                           config.Database.password))
    success = False
    cursor = connection.cursor()
    try:
        cursor.execute(sql_commands)
        connection.commit()
        success = True
    except psycopg.Error:
        logger.exception()
        connection.rollback()
        success = False
    cursor.close()
    return success


def drop_tables(database):
    drop_state(database, "tested_ok_ins")
    drop_state(database, "fixed_ins")
    drop_state(database, "reported_ins")
    drop_state_value(database, "versions")
    drop_state(database, "keywords")
    drop_state_value(database, "keyword_values")
    drop_state(database, "categories")
    drop_state_value(database, "category_values")
    drop_state(database, "priorities")
    drop_state_value(database, "priority_values")
    drop_comments(database)
    drop_bugs(database)
    drop_statuses(database)
    drop_users(database)


def create_tables(database):
    create_users(database)
    create_statuses(database)
    create_bugs(database)
    create_comments(database)
    create_state_value(database, "priority_values")
    create_state(database, "priorities", "priority_values")
    create_state_value(database, "category_values")
    create_state(database, "categories", "category_values")
    create_state_value(database, "keyword_values")
    create_state(database, "keywords", "keyword_values")
    create_state_value(database, "versions")
    create_state(database, "reported_ins", "versions")
    create_state(database, "fixed_ins", "versions")
    create_state(database, "tested_ok_ins", "versions")


def have_tables(database):
    return have_table(database, "users")


def have_table(database, table):
    connection = psycopg.connect(
        "dbname=%s user=%s password=%s" % (database,
                                           config.Database.user,
                                           config.Database.password))
    success = False
    cursor = connection.cursor()
    try:
        cursor.execute("""
                SELECT * FROM %s;
        """ % table)
        success = True
    except psycopg.Error:
        success = False
    cursor.close()
    return success

    
def create_users(database):
    # Users who can file bugs and make changes.
    # The user id is unique and never reused (even if user is deleted).
    # Usernames must also be unique. Note that deleting a user and creating
    # a new user of the same username is given a new user_id.
    return run_sql(database, """
        CREATE SEQUENCE user_ids_seq;
        CREATE TABLE users (user_id INTEGER
                                    PRIMARY KEY 
                                    DEFAULT nextval('user_ids_seq'),
                            username TEXT UNIQUE,
                            password TEXT,
                            name TEXT,
                            email TEXT);
                            """)

def drop_users(database):
    return run_sql(database, """
        DROP TABLE users;
        DROP SEQUENCE user_ids_seq;
        """)

def create_statuses(database):
    return run_sql(database, """
        CREATE SEQUENCE statuses_ids_seq;
        CREATE TABLE statuses (status_id INTEGER
                                         PRIMARY KEY
                                         DEFAULT nextval('statuses_ids_seq'),
                               name TEXT);
        INSERT INTO statuses (name) VALUES ('new');
        INSERT INTO statuses (name) VALUES ('reviewed');
        INSERT INTO statuses (name) VALUES ('scheduled');
        INSERT INTO statuses (name) VALUES ('fixed');
        INSERT INTO statuses (name) VALUES ('closed');
        """)

def drop_statuses(database):
    return run_sql(database, """
        DROP TABLE statuses;
        DROP SEQUENCE statuses_ids_seq;
        """)

def create_bugs(database):
    # Each bug may have no comments or states, but it must have a unique id,
    # a title, and details of who filed it and when.
    return run_sql(database, """
        CREATE SEQUENCE bug_ids_seq;
        CREATE TABLE bugs (bug_id INTEGER
                                  PRIMARY KEY
                                  DEFAULT nextval('bug_ids_seq'),
                           user_id INTEGER
                                   NOT NULL
                                   REFERENCES users (user_id),
                           date TIMESTAMP,
                           title TEXT,
                           status_id INTEGER
                                     NOT NULL
                                     REFERENCES statuses (status_id));
                           """)

def drop_bugs(database):
    return run_sql(database, """
        DROP TABLE bugs;
        DROP SEQUENCE bug_ids_seq;
        """)

def create_comments(database):
    # Each bug has zero or more comments (accumulated over time).
    # Once a comment has been created, it cannot be changed.
    return run_sql(database, """
        CREATE TABLE comments (bug_id INTEGER
                                      NOT NULL
                                      REFERENCES bugs (bug_id),
                               user_id INTEGER
                                       NOT NULL
                                       REFERENCES users (user_id),
                               date TIMESTAMP,
                               comment TEXT);
                               """)

def drop_comments(database):
    return run_sql(database, """
        DROP TABLE comments;
        """)


def create_state_value(database, value_table):
    return run_sql(database, """
        CREATE SEQUENCE %(value_table)s_ids_seq;
        CREATE TABLE %(value_table)s
                (id INTEGER
                    PRIMARY KEY
                    DEFAULT nextval('%(value_table)s_ids_seq'),
                 name TEXT
                      UNIQUE);
        """ % {"value_table":value_table})


def create_state(database, bug_table, value_table):
    return run_sql(database, """
        CREATE TABLE %(bug_table)s
                (bug_id INTEGER
                        NOT NULL
                        UNIQUE
                        REFERENCES bugs (bug_id),
                 id INTEGER
                    NOT NULL
                    REFERENCES %(value_table)s (id));
        """ % {"bug_table":bug_table, "value_table":value_table})


def drop_state_value(database, value_table):
    return run_sql(database, """
        DROP TABLE %(value_table)s;
        DROP SEQUENCE %(value_table)s_ids_seq;
        """ % {"value_table":value_table})


def drop_state(database, bug_table):
    return run_sql(database, """
        DROP TABLE %(bug_table)s;
        """ % {"bug_table":bug_table})

