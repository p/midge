# $Id$
# (C) Timothy Corbett-Clark, 2004


import distutils.core


distutils.core.setup(
    name="midge",
    version="0.1",
    description="A small but powerful bug tracking system",
    author="Timothy Corbett-Clark",
    author_email="tcorbettclark@sourceforge.net",
    url="http://midge.sourceforge.net",
    packages=["midge"],
    data_files=[("/etc", ["etc/midge.conf"]),
                ("/usr/local/share/midge",
                 ["images/up.gif", "images/down.gif"])])