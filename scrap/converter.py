# $Id$
# (C) Timothy Corbett-Clark, 2004

import csv

if __name__ == "__main__":

    print "Converting users...",
    users = eval(file("users.txt").read())
    f = file("users.csv", "w")
    writer = csv.writer(f)
    writer.writerow( ("Username", "Name", "Email", "Password") )
    for username, name, email in users:
        writer.writerow( (username, name, email, username) )
    f.close()
    print "done"
    
    print "Converting bugs...",
    bugs = eval(file("bugs.txt").read())
    f = file("bugs.csv", "w")
    writer = csv.writer(f)
    writer.writerow( ("Bug", "Username", "Date", "Title", "Status", "Priority",
                      "Category", "Keyword",
                      "Reported in", "Fixed in", "Tested ok in") )
    for row in bugs:
        writer.writerow(row)
    f.close()
    print "done"
        
    print "Converting comments...",
    comments = eval(file("comments.txt").read())
    f = file("comments.csv", "w")
    writer = csv.writer(f)
    writer.writerow( ("Bug", "Username", "Date", "Comment") )
    for row in comments:
        writer.writerow(row)
    f.close()
    print "done"
