# $Id$
# (C) Timothy Corbett-Clark, 2004


import distutils.core


distutils.core.setup(
    name="midge",
    version="0.1",
    description="A small but powerful bug tracking system",
    author="Timothy Corbett-Clark",
    author_email="tcorbettclark@users.sourceforge.net",
    url="http://midge.sourceforge.net",
    packages=["midge"],
    data_files=[("/etc", ["etc/midge.conf"]),
                ("/etc/init.d", ["etc/init.d/midge"]),
                ("/usr/local/bin", ["bin/midged",
                                    "bin/midge-test",
                                    "bin/midge-config",
                                    "bin/midge-export",
                                    "bin/midge-import"]),
                ("/usr/local/sbin", ["bin/midge-admin"]),
                ("/usr/local/share/midge",
                 ["share/up.gif",
                  "share/down.gif",
                  "share/default.css"])])
