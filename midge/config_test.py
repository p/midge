# $Id$
# (C) Timothy Corbett-Clark, 2004

import sys
import unittest

import midge.config
import midge.lib


class ConfigTests(unittest.TestCase):

    def test_can_read_config(self):
        """Check read config"""
        midge.config.read()
        self.assertNotEqual(midge.config.Postgres.admin_user, None)
        self.assertNotEqual(midge.config.Database.user, None)
        self.assertNotEqual(midge.config.Database.password, None)
        self.assertNotEqual(midge.config.Database.name, None)
        self.assertNotEqual(midge.config.Database.test_name, None)
        self.assertNotEqual(midge.config.Project.name, None)
        self.assertNotEqual(midge.config.Server.interface, None)
        self.assertNotEqual(midge.config.Server.port, None)
        self.assertNotEqual(midge.config.Server.session_timeout, None)
        self.assertNotEqual(midge.config.Server.maintenance_period, None)
        self.assertNotEqual(midge.config.Server.debugging, None)
        self.assertNotEqual(midge.config.Email.smtp_host, None)
        self.assertNotEqual(midge.config.Email.from_address, None)
        self.assertNotEqual(midge.config.Presentation.directory, None)

    def test_can_print_env_variables(self):
        """Check print config as bash env variables"""
        midge.config.read()

        class MyStdout:
            lines = []
            def write(self, line):
                line = line.strip()
                if line:
                    self.lines.append(line)
                
        sys.stdout = MyStdout() 
        midge.config.print_env_variables()
        self.assertEqual(len(sys.stdout.lines), 13)
        sys.stdout = sys.__stdout__
