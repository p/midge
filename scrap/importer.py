# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Functionality to import bugs from files."""

import midge.config
import midge.connection
import midge.io

midge.config.read()

connection = midge.connection.Connection()
importer = midge.io.Importer(connection)

print "Importing users..."
users = eval(file("users.txt").read())
for username, name, email in users:
    importer.import_user(username, name, email, username)


print "Importing bugs..."
bugs = eval(file("bugs.txt").read())
for row in bugs:
    importer.import_bug(*row)


print "Importing comments..."
comments = eval(file("comments.txt").read())
for row in comments:
    importer.import_comment(*row)

connection.commit()
connection.close()
print "Done."
