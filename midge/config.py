# $Id$
# (C) Timothy Corbett-Clark, 2004


import ConfigParser
import re

import midge.logger as logger


class Postgres:

    admin_user = None


class Database:

    user = None
    password = None
    name = None
    test_name = None


class Project:

    name = None
    help = None


class Server:

    interface = None
    port = None
    session_timeout = None
    maintenance_period = None
    

class Email:

    from_address = None
    smtp_host = None
    

class Logging:

    host = None
    facility = None
    debugging = None
    

class Presentation:

    directory = None


class CommentMappings:

    mappings = None

    
def read():
    """Read the config files.

    Must be called before attempting to use any configuration data!

    """
    config = ConfigParser.SafeConfigParser()

    def get(section, option):
        try:
            return config.get(section, option)
        except Exception:
            logger.exception()
            raise

    def items(section):
        try:
            return config.items(section)
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

    config.read(["/etc/midge.conf"])
    Postgres.admin_user = get("Postgres", "admin_user")
    Database.user = get("Database", "user")
    Database.password = get("Database", "password")
    Database.name = get("Database", "name")
    Database.test_name = get("Database", "test_name")
    Project.name = get("Project", "name")
    Project.help = get("Project", "help")
    Server.interface = get("Server", "interface")
    Server.port = get_int("Server", "port")
    Server.session_timeout = get_int("Server", "session_timeout")
    Server.maintenance_period = get_int("Server", "maintenance_period")
    Email.from_address = get("Email", "from_address")
    Email.smtp_host = get("Email", "smtp_host")
    Logging.host = get("Logging", "host")
    Logging.facility = get("Logging", "facility")
    Logging.debugging = get_boolean("Logging", "debugging")
    Presentation.directory = get("Presentation", "directory")

    def read_comment_mappings():
        separator = get("Comment Mappings", "SEPARATOR").strip()
        mappings = []
        for k,v in items("Comment Mappings"):
            if k != "separator":
                pattern, substitute = v.split(separator, 1)
                mappings.append(
                    (re.compile( pattern.strip()), substitute.strip()) )
        mappings.sort()
        CommentMappings.mappings = mappings

    read_comment_mappings()
    

def print_env_variables():
    """Print the variables to standard out in bash format."""
    for cls in (Postgres, Database, Project, Server, Email, Logging):
        for name in dir(cls):
            if not name.startswith("__"):
                print "%s_%s=%s" % (cls.__name__.upper(),
                                    name.upper(),
                                    getattr(cls, name))
