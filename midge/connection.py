# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Provide abstract connections and test connections to the database."""

import psycopg

import midge.administration as administration
import midge.config as config
import midge.lib as lib
import midge.logger as logger


class Connection(object):

    """Provide an abstracted connection to the database.

    Also automatically sets-up the tables if they are not present.
    
    """
    def __init__(self):
        self._connection = psycopg.connect(
            "dbname=%s user=%s password=%s" % (config.Database.name,
                                               config.Database.user,
                                               config.Database.password))
        self._setup_tables()

    def _setup_tables(self):
        if not administration.have_tables(config.Database.name):
            logger.info("No tables defined - creating new ones")
            administration.create_tables(config.Database.name)

    def cursor(self):
        return self._connection.cursor()

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()

    
class TestConnection(object):

    """A connection for testing which is independent of a normal Connection.

    This TestConnection behaves the same as a vanilla Connection
    except that it sets up new (empty) tables on every construction.

    """
    def __init__(self):
        self._drop_tables()
        self._create_tables()
        self._create_test_user()
        self._connection = psycopg.connect(
            "dbname=%s user=%s password=%s" % (config.Database.test_name,
                                               config.Database.user,
                                               config.Database.password))

    def _create_tables(self):
        if not administration.have_tables(config.Database.test_name):
            administration.create_tables(config.Database.test_name)

    def _drop_tables(self):
        if administration.have_tables(config.Database.test_name):
            administration.drop_tables(config.Database.test_name)

    def _create_test_user(self):
        administration.run_sql(
            config.Database.test_name,
            "INSERT INTO users (username, password, name, email) "
            "VALUES ('test-username', 'test-password', "
            "'test-name', 'test-email')")

    def cursor(self):
        return self._connection.cursor()

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        self._connection.close()
        self._drop_tables()


# Expose those exceptions which users of this module may wish to catch.
#Error = psycopg.Error
#DataError = psycopg.DataError
#DatabaseError = psycopg.DatabaseError
ProgrammingError = psycopg.ProgrammingError
IntegrityError = psycopg.IntegrityError

