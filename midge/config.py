# $Id$
# (C) Timothy Corbett-Clark, 2004


import ConfigParser

import midge.logger as logger


class Postgres:

    path = None
    admin_user = None


class Database:

    user = None
    password = None
    name = None
    test_name = None


class Project:

    name = None


class Server:

    interface = None
    port = None
    session_timeout = None
    debugging = None


class Email:

    from_address = None
    smtp_host = None
    

class Images:

    directory = None

    
def read():
    """Read the config files.

    Must be called before attempting to use any configuration data!

    """
    config = ConfigParser.SafeConfigParser()
    config.read(["midge.conf",
                 "../midge.conf",
                 "/usr/local/etc/midge.conf",
                 "/etc/midge.conf"])

    def get(section, option):
        try:
            return config.get(section, option)
        except Exception:
            logger.exception()
            raise

    def get_int(section, option):
        try:
            return config.getint(section, option)
        except Exception:
            logger.exception()
            raise

    def get_boolean(section, option):
        try:
            return config.getboolean(section, option)
        except Exception:
            logger.exception()
            raise

    Postgres.path = get("Postgres", "path")
    Postgres.admin_user = get("Postgres", "admin_user")
    Database.user = get("Database", "user")
    Database.password = get("Database", "password")
    Database.name = get("Database", "name")
    Database.test_name = get("Database", "test_name")
    Project.name = get("Project", "name")
    Server.interface = get("Server", "interface")
    Server.port = get_int("Server", "port")
    Server.session_timeout = get_int("Server", "session_timeout")
    Server.debugging = get_boolean("Server", "debugging")
    Email.from_address = get("Email", "from_address")
    Email.smtp_host = get("Email", "smtp_host")
    Images.directory = get("Images", "directory")


def print_env_variables():
    """Print the variables to standard out in bash format."""
    for cls in (Postgres, Database, Project, Server, Email):
        for name in dir(cls):
            if not name.startswith("__"):
                print "%s_%s=%s" % (cls.__name__.upper(),
                                    name.upper(),
                                    getattr(cls, name))
