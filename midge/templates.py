# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Functions for generating html."""

import re

import midge.config as config
import midge.lib as lib


def format_comment(text):
    """Return text suitable for displaying as comment.

    This means:
      stripping leading newlines (but not spaces)
      stripping tailing whitespace
      escaping any html-like tags,
      replacing newlines with <br/>, and
      replacing leading spaces with hardspaces (&nbsp;).

    Also replace text to provide hyperlinks, as per midge.conf.

    """
    text = text.lstrip("\n")
    text = text.rstrip()
    text = lib.html_entity_escape(text)
    rows = []
    for row in text.split("\n"):
        n_leading_spaces = 0
        for c in row:
            if c == " ":
                n_leading_spaces += 1
            else:
                break
        rows.append(row.replace(" ", "&nbsp;", n_leading_spaces))
    text = "<br/>".join(rows)

    for pattern, substitute in config.CommentMappings.mappings:
        text = re.sub(pattern, substitute, text)

    return text


def get_version():
    version = None
    name = "$Name$"
    if ":" in name:
        version = name.split(":")[1][:-1].strip()
    if version:
        return version
    else:
        return "&lt;unknown&gt;"


def header(wfile, title=None):
    if title:
        title = "%s - Midge (%s)" % (title, config.Project.name)
    else:
        title = "Midge (%s)" % config.Project.name
    wfile.write('''
<html>
 <head>
  <title>%(title)s</title>
  <style>
  .nowrap {
    white-space:nowrap;
  }
  .expand {
    width: 100%%;
  }
  </style>
 </head>
 <body bgcolor="#ffffff">
  <form action="view">
   <table cellspacing="0" cellpadding="3" border="0" width="100%%">
    <tr>
     <td>
      <b>Midge</b> for project <b>%(project)s</b>
     </td>
     <td align="right">
      <font size="-1">
       <a href="login">Login</a> |
       <a href="adduser">Create new account</a> |
       <a href="modifyuser">Modify user account</a> |
       <a href="logout">Logout</a>
      </font>
     </td>
    </tr>
   </table>
   <table cellspacing="0" cellpadding="3" border="0" width="100%%">
    <tr bgcolor="#FFCC55">
     <td>
      <a href="home">Home</a> | 
      <a href="new">Add new bug</a> | 
      <a href="list">List bugs</a> | 
      <a href="search">Search bugs</a> | 
        Find bug <input size="5" name="bug_id" type="text"/>
      <input type="submit" value="Go"/>
     </td>
    </tr>
   </table>
  </form>
''' % {"title": title, "project":config.Project.name})

def vspace(wfile):
    wfile.write("<br/>")

def hrule(wfile):
    wfile.write("<hr/>")

def title(wfile, title, title2=None):
    if title2:
        wfile.write('<font size="+1"><b>%s</b></font> - %s' % (title, title2))
    else:
        wfile.write('<h2>%s</h2>' % title)
        
def table(wfile, titles, rows):
    wfile.write('''
<p></p>
<table cellpadding="2" cellspacing="3" border="0">
 <tr>''')
    for url, name in titles:
        wfile.write('''
  <th bgcolor="#cecece">
   <a href="%s">%s</a>
  </th>''' % (url, name))
    wfile.write('''
 </tr>''')
    colours = ("#d5dfef", "#eeeeee")
    colour_index = 0
    for row in rows:
        wfile.write('''
 <tr>''')
        for entry in row:
            wfile.write('''
  <td bgcolor="%s">%s</td>''' % (colours[colour_index], entry))
        wfile.write('''
 </tr>''')
        colour_index = (colour_index + 1) % 2
    wfile.write('''
</table>''')

def paragraph(wfile, text):
    wfile.write('<p>')
    wfile.write(text)
    wfile.write('</p>')

def bullets(wfile, *items):
    wfile.write('<ul>')
    for text in items:
        wfile.write('<li>%s</li>' % text)
    wfile.write('</ul>')

def possible_actions(wfile, *possible_actions):
    wfile.write('<ul>')
    for href, label in possible_actions:
        wfile.write('<li><a href="%s">%s</a></li>' % (href, label))
    wfile.write('</ul>')

def footer(wfile):
    wfile.write('''
  <p></p>
  <form action="view" name="main">
   <table cellspacing="0" cellpadding="3" border="0" width="100%%">
    <tr bgcolor="#FFCC55">
    <td>
     <a href="home">Home</a> | 
     <a href="new">Add new bug</a> | 
     <a href="list">List bugs</a> | 
     <a href="search">Search bugs</a> | 
        Find bug <input size="5" name="bug_id" type="text"/>
      <input type="submit" value="Go"/>
    </td>
   </tr>
  </table>
  <table cellspacing="0" cellpadding="3" border="0" width="100%%">
   <tr>
    <td valign="top">
      <font size="-2">
       <em>Version %(version)s.</em>
       See <a href="http://midge.sourceforge.net">
        http://midge.sourceforge.net</a> for updates.
      </font>
     </td>
     <td valign="top" align="right">
      <font size="-2">
       Copyright &copy; 2004, Timothy Corbett-Clark.<br/>
      </font>   
     </td>
    </tr>
   </table>
  </form>
 </body>
</html>''' % {"version": get_version()})


def login_form(wfile, path, usernames):
    wfile.write('''
  <center><blockquote>
   <form action="%s" method="POST">
    <table cellpadding="5" cellspacing="0" border="0">
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Username</b></small></td>
      <td>
       <select name="username">
        <option value=""></option>''' % path)
    for username in usernames:
        wfile.write('''
        <option value="%(username)s">%(username)s</option>'''
                    % {"username": username})
    wfile.write('''
       </select>
      </td>
     </tr>
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Password</b></small></td>
      <td>
       <input type="password" name="password"/>
      </td>
     </tr>
     <tr>
      <td colspan="3" align="right">
       <input type="submit" value="Login"/>
      </td>
     </tr>
    </table>
   </form>
  </blockquote></center>''')


def add_user_form(wfile, path):
    wfile.write('''
  <center><blockquote>
   <form action="%(path)s" method="POST">
    <table cellpadding="5" cellspacing="0" border="0">
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Username</b></small></td>
      <td>
       <input type="text" size="40" name="username"/>
      </td>
     </tr>
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Name</b></small></td>
      <td>
       <input type="text" size="40" name="name"/>
      </td>
     </tr>
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Email</b></small></td>
      <td>
       <input type="text" size="40" name="email"/>
      </td>
     </tr>
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Password</b></small></td>
      <td>
       <input type="password" size="40" name="password"/>
      </td>
     </tr>
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Password (again)</b></small></td>
      <td>
       <input type="password" size="40" name="password_again"/>
      </td>
     </tr>
     <tr><td><table></table></td></tr>
     <tr>
      <td colspan="3" align="right">
       <input type="submit" value="Create account"/>
      </td>
     </tr>
    </table>
   </form>
  </blockquote></center>''' % {"path": path})


def modify_user_form(wfile, path, name, email):
    wfile.write('''
  <center><blockquote>
   <form action="%(path)s" method="POST">
    <table cellpadding="5" cellspacing="0" border="0">
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Name</b></small></td>
      <td>
       <input type="text" size="40" name="name" value="%(name)s"/>
      </td>
     </tr>
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Email</b></small></td>
      <td>
       <input type="text" size="40" name="email" value="%(email)s"/>
      </td>
     </tr>
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Existing Password</b></small></td>
      <td>
       <input type="password" size="40" name="password"/>
      </td>
     </tr>

     <tr><td><table></table></td></tr>
      
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>New password</b></small></td>
      <td>
       <input type="password" size="40" name="new_password"/>
      </td>
     </tr>
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>New password (again)</b></small></td>
      <td>
       <input type="password" size="40" name="new_password_again"/>
      </td>
     </tr>
     <tr><td><table></table></td></tr>
     <tr>
      <td colspan="3" align="right">
       <input type="submit" value="Change details"/>
      </td>
     </tr>
    </table>
   </form>
  </blockquote></center>''' % {"path": path, "name": name, "email": email})


def new_bug_form(wfile, path, versions, configurations, categories):
    wfile.write('''
  <center><blockquote>
   <form action="%(path)s" method="POST">
    <table cellpadding="5" cellspacing="0" border="0">
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Title</b></small></td>
      <td colspan="3">
       <input type="text" size="80" maxlength="80" name="title"/>
      </td>
     </tr>
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Version</b></small></td>
      <td>
       <select name="version" size="1">''' % {"path": path})
    for version in versions:
        if version == "":
            wfile.write('''
        <option value="" selected="selected"></option>''')
        else:
            wfile.write('''
        <option value="%s">%s</option>''' % (version, version))
    wfile.write('''
       </select>
      </td>
      <td align="right"><small>(or use a new version</small>
       <input type="text" name="new_version"/><small>)</small>
      </td>
     </tr>
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Category</b></small></td>
      <td>
       <select name="category" size="1">''')
    for category in categories:
        if category == "":
            wfile.write('''
        <option value="" selected="selected"></option>''')
        else:
            wfile.write('''
        <option value="%s">%s</option>''' % (category, category))
    wfile.write('''
       </select>
      </td>
      <td align="right"><small>(or use a new category</small>
       <input type="text" name="new_category"/><small>)</small>
      </td>
     </tr>
     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Configuration</b></small></td>
      <td>
       <select name="configuration" size="1">''')
    for configuration in configurations:
        if configuration == "":
            wfile.write('''
        <option value="" selected="selected"></option>''')
        else:
            wfile.write('''
        <option value="%s">%s</option>''' % (configuration, configuration))
    wfile.write('''
       </select>
      </td>
      <td align="right"><small>(or use a new configuration</small>
       <input type="text" name="new_configuration"/><small>)</small>
      </td>
     </tr>

     <tr bgcolor="#DDDDDD">
      <td valign="baseline"><small><b>Description</b></small></td>
      <td colspan="3">
       <textarea name="description" cols="70" rows="8"></textarea>
      </td>
     </tr>
     <tr><td><table></table></td></tr>
     <tr>
      <td colspan="3" align="right">
       <input type="submit" value="Submit"/>
      </td>
     </tr>
    </table>
   </form>
  </blockquote></center>''')


class StatusHints(object):

    new = ("(set to <b>scheduled</b> to fix now, <b>reviewed</b> to "
           "fix later, or <b>close</b> if not a bug)")

    reviewed = "(set to <b>scheduled</b> to have this bug fixed now)"

    scheduled = "(set to <b>fixed</b> once ready for testing)"

    fixed = ("(set to <b>closed</b> once confirmed fixed, or "
             "<b>scheduled</b> if still broken)")

    closed = ""


def show_comments(wfile, bug):
    for comment in bug.comments:
        wfile.write('''
  <table width="100%%">
   <tr bgcolor="#CCCCCC">
    <td>
     <font size="-1">
      Posted by <b>%(name)s</b> (%(username)s) on
                <b>%(date)s</b> at
                <b>%(time)s</b>
     </font>
   </td>
   </tr>
  </table>
  <tt>%(text)s</tt>
  <br/><br/>
  ''' % {"name": comment.users_name,
         "username": comment.username,
         "date":lib.format_date(comment.date),
         "time":lib.format_time(comment.date),
         "text":format_comment(comment.text)})


def bug_status_summary(wfile, bug):
    if bug.priority:
        wfile.write('''
  <p>
   <strong>Bug %(bug_id)s, %(status)s,
   priority %(priority)s</strong> (<a href="#editbugform">more</a>)
  </p>''' % {"bug_id": bug.bug_id,
             "status": bug.status,
             "priority": bug.priority})
    else:
        wfile.write('''
  <p>
   <strong>Bug %(bug_id)s, %(status)s</strong>
   (<a href="#editbugform">more</a>)
  </p>''' % {"bug_id": bug.bug_id,
             "status": bug.status.capitalize()})
  
    
def edit_bug_form(wfile, path, bug, statuses, priorities,
                  configurations, categories, keywords, versions):
    wfile.write('''
  <center><blockquote>
  <a name="editbugform" id="editbugform"></a>
  <form action="%(path)s" method="POST">
  <input type="hidden" name="bug_id" value="%(bug_id)s"/>
  <table cellpadding="3" cellspacing="0" border="0">
   <tr>
    <td bgcolor="#EEEEEE"><small><em>States</em></small></td>
   </tr> 
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Status</b></small></td>
    <td>
     <select name="status" size="1">''' % {"bug_id":bug.bug_id, "path": path})
    for status in statuses:
        if bug.status == status:
            wfile.write('''
      <option value="%s" selected="selected">%s</option>''' % (status, status))
        else:
            wfile.write('''
      <option value="%s">%s</option>''' % (status, status))
    wfile.write('''
     </select>
    </td>
    <td align="right">
     <small>
       %s
     </small>
    </td>
   </tr>
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Priority</b></small></td>
    <td>
     <select name="priority" size="1">''' % getattr(StatusHints, bug.status))
    for priority in priorities:
        if bug.priority == priority:
            wfile.write('''
      <option value="%s" selected="selected">%s</option>''' % (priority, priority))
        else:
            wfile.write('''
      <option value="%s">%s</option>''' % (priority, priority))
    wfile.write('''
     </select>
    </td>
    <td align="right">
     <small>
      (<b>1</b> is lowest, <b>5</b> is highest)
     </small>
    </td>
   </tr>
  
   <tr><td><table></table></td></tr>
   <tr><td><table></table></td></tr>
  
   <tr>
    <td bgcolor="#EEEEEE"><small><em>Groupings</em></small></td>
   </tr> 
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Category</b></small></td>
    <td>
     <select name="category" size="1">''')
    for category in categories:
        if bug.category == category:
            wfile.write('''
      <option value="%s" selected="selected">%s</option>''' % (category, category))
        else:
            wfile.write('''
      <option value="%s">%s</option>''' % (category, category))
    wfile.write('''
     </select>
    </td>
    <td align="right"><small>(or use a new category</small>
        <input type="text" name="new_category"></input><small>)</small>
    </td>
   </tr>
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Configuration</b></small></td>
    <td>
     <select name="configuration" size="1">''')
    for configuration in configurations:
        if configuration == bug.configuration:
            wfile.write('''
      <option value="%s" selected="selected">%s</option>''' % (
                configuration, configuration))
        else:
            wfile.write('''
      <option value="%s">%s</option>''' % (
                configuration, configuration))
    wfile.write('''
     </select>
    </td>
    <td align="right"><small>(or use a new configuration</small>
        <input type="text" name="new_configuration"></input><small>)</small>
    </td>
   </tr>
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Keyword</b></small></td>
    <td>
     <select name="keyword" size="1">''')
    for keyword in keywords:
        if keyword == bug.keyword:
            wfile.write('''
      <option value="%s" selected="selected">%s</option>''' % (
                keyword, keyword))
        else:
            wfile.write('''
      <option value="%s">%s</option>''' % (
                keyword, keyword))
    wfile.write('''
     </select>
    </td>
    <td align="right"><small>(or use a new keyword</small>
        <input type="text" name="new_keyword"></input><small>)</small>
    </td>
   </tr>
 
   <tr><td><table></table></td></tr>
   <tr><td><table></table></td></tr>
  
   <tr>
    <td bgcolor="#EEEEEE"><small><em>Versions</em></small></td>
   </tr> 
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Reported in</b></small></td>
    <td>
     <select name="reported_in" size="1">''')
    for version in versions:
        if version == bug.reported_in:
            wfile.write('''
         <option value="%s" selected="selected">%s</option>''' % (version, version))
        else:
            wfile.write('''
         <option value="%s">%s</option>''' % (version, version))
    wfile.write('''
     </select>
    </td>
    <td align="right"><small>(or use a new version</small>
        <input type="text" name="new_reported_in"></input><small>)</small>
    </td>
   </tr>
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Fixed in</b></small></td>
    <td>
     <select name="fixed_in" size="1">''')
    for version in versions:
        if version == bug.fixed_in:
            wfile.write('''
         <option value="%s" selected="selected">%s</option>''' % (version, version))
        else:
            wfile.write('''
         <option value="%s">%s</option>''' % (version, version))
    wfile.write('''
     </select>
    </td>
    <td align="right"><small>(or use a new version</small>
        <input type="text" name="new_fixed_in"></input><small>)</small>
    </td>
   </tr>
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Tested ok in</b></small></td>
    <td>
     <select name="tested_ok_in" size="1">
     ''')
    for version in versions:
        if version == bug.tested_ok_in:
            wfile.write('''
         <option value="%s" selected="selected">%s</option>''' % (version, version))
        else:
            wfile.write('''
         <option value="%s">%s</option>''' % (version, version))
    wfile.write('''
     </select>
    </td>
    <td align="right"><small>(or use a new version</small>
        <input type="text" name="new_tested_ok_in"></input><small>)</small>
    </td>
   </tr>
  
   <tr><td><table></table></td></tr>
   <tr><td><table></table></td></tr>
  
   <tr>
    <td bgcolor="#EEEEEE"><small><em>Add comment</em></small></td>
   </tr> 
   <tr bgcolor="#DDDDDD">
    <td colspan="3">
     <textarea name="comment" cols="80" rows="8"></textarea>
    </td>
   </tr>
  
   <tr><td><table></table></td></tr>
  
   <tr>
    <td colspan="3" align="right">
     <input type="submit" value="Submit"/>
    </td>
   </tr>
  </table>
  </form>
  </blockquote></center>''')
  

def list_form(wfile, path, status_counts):
    def plural(n):
        if n == 1:
            return ""
        else:
            return "s"
        
    wfile.write('''
  <center><blockquote>  
   <form action="%(path)s">
    <table bgcolor="#DDDDDD" cellpadding="8" cellspacing="0" border="0">
     <tr>
      <td>
       <input type="radio" name="status" value="new" checked="checked"/>
       %(n_new)s
      </td>
      <td><b>new</b> bug%(new_plural)s in need of review</td>
     </tr>
     <tr>
      <td>
       <input type="radio" name="status" value="reviewed"/>
       %(n_reviewed)s
      </td>
      <td><b>reviewed</b> bug%(reviewed_plural)s ready to be scheduled</td>
     </tr>
     <tr>
      <td>
       <input type="radio" name="status" value="scheduled"/>
       %(n_scheduled)s
      </td>
      <td><b>scheduled</b> bug%(scheduled_plural)s waiting to be fixed</td>
     </tr>
     <tr>
      <td>
       <input type="radio" name="status" value="fixed"/>
       %(n_fixed)s
      </td>
      <td><b>fixed</b> bug%(fixed_plural)s waiting to be tested</td>
     </tr>
     <tr>
      <td>
       <input type="radio" name="status" value="closed"/>
       %(n_closed)s
      </td>
      <td><b>closed</b> bug%(closed_plural)s</td>
     </tr>
     <tr align="right" valign="bottom" bgcolor="#FFFFFF">
      <td colspan="2" align="right">
       <input type="submit" value="List bugs"/>
      </td>
     </tr>
    </table>
   </form>
  </blockquote></center>''' %
                {"path": path,
                 "n_new": status_counts.new,
                 "n_reviewed": status_counts.reviewed,
                 "n_scheduled": status_counts.scheduled,
                 "n_fixed": status_counts.fixed,
                 "n_closed": status_counts.closed,
                 "new_plural": plural(status_counts.new),
                 "reviewed_plural": plural(status_counts.reviewed),
                 "scheduled_plural": plural(status_counts.scheduled),
                 "fixed_plural": plural(status_counts.fixed),
                 "closed_plural": plural(status_counts.closed),
                 })


def _table_headings(wfile, path, titles,
                    variables, sorted_by, ordered):
    wfile.write('''
    <tr>''')
    for heading, variable in zip(titles, variables):
        if variable == sorted_by:
            new_order = {"ascending": "descending",
                         "descending": "ascending"}[ordered]
        else:
            new_order = "ascending"
        url = lib.html_entity_escape(
            lib.join_url(path, {"sort_by": variable,
                                "order": new_order}))
        if variable == variables[-1]:
            css_class = "expand"
        else:
            css_class = "nowrap"
        wfile.write('''
     <th class="%(css_class)s" bgcolor="#cecece">
      <a href="%(url)s"><font size="-2">
       %(heading)s
      </font></a>''' % {"heading": heading,
                        "url": url,
                        "css_class": css_class})
        if variable == sorted_by:
            direction = {"ascending": "up",
                         "descending": "down"}[ordered]
            wfile.write('''
      <img src="/images?name=%(direction)s.gif" alt="%(direction)s"/>''' % {"direction": direction})
        wfile.write('''
     </th>''')
    wfile.write('''                
    </tr>''')

def _table_rows(wfile, rows):
    colours = ("#d5dfef", "#eeeeee")
    colour_index = 0
    for row in rows:
        wfile.write('''
    <tr>''')
        for variable, value in row.get():
            if variable == "bug_id":
                wfile.write('''
     <td bgcolor="%(colour)s">
      <font size="-1">
       <a href="/view?bug_id=%(bug_id)s">%(bug_id)s</a>
      </font>
     </td>
  ''' % {"colour": colours[colour_index],
         "bug_id": row.bug_id})
            else:
                wfile.write('''
     <td bgcolor="%(colour)s">
      <font size="-1">
       %(value)s
      </font>
     </td>
  ''' % {"colour": colours[colour_index],
         "value": value})
        wfile.write('''
    </tr>''') 
        colour_index = (colour_index + 1) % 2

def table_of_bugs(wfile, path, search):
    assert len(search.rows) > 0
    titles = search.titles
    variables = search.variables
    sorted_by = search.sort_by
    ordered = search.order
    wfile.write('''
  <center>
   <table cellpadding="2" cellspacing="3" border="0">''')
    _table_headings(wfile, path, titles,
                    variables, sorted_by, ordered)
    _table_rows(wfile, search.rows)
    wfile.write('''
   </table>
  </center>''')


def search_form(wfile, path, statuses, priorities,
                configurations, categories, keywords, versions):
    wfile.write('''
  <center><blockquote>
  <form action="%(path)s">
  <table cellpadding="3" cellspacing="0" border="0">
   <tr>
    <td bgcolor="#EEEEEE"><small><em>Text</em></small></td>
   </tr> 
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Title</b></small></td>
    <td>
     <input name="title" type="text"/>
    </td>
   </tr>
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Comments</b></small></td>
    <td>
     <input name="comments" type="text"/>
    </td>
   </tr>

   <tr><td><table></table></td></tr>
   <tr><td><table></table></td></tr>
  
   <tr>
    <td bgcolor="#EEEEEE"><small><em>States</em></small></td>
   </tr> 
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Status</b></small></td>
    <td>
     <select name="status" size="1">''' % {"path": path})
    for status in statuses:
        wfile.write('''
      <option value="%s">%s</option>''' % (status, status))
    wfile.write('''
     </select>
    </td>
    <td>
     <small>&nbsp;(regex</small>
     <input type="text" name="status_regex"/>
     <small>)</small>
    </td>
    <td bgcolor="#FFFFFF">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" name="status_column" value="on">Show column
      </input>
     </label></small>
    </td>
   </tr>
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Priority</b></small></td>
    <td>
     <select name="priority" size="1">''')
    for priority in priorities:
        wfile.write('''
      <option value="%s">%s</option>''' % (priority, priority))
    wfile.write('''
     </select>
    </td>
    <td>
     <small>&nbsp;(regex</small>
     <input type="text" name="priority_regex"/>
     <small>)</small>
    </td>
    <td bgcolor="#FFFFFF">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" name="priority_column" value="on">Show column
      </input>
     </label></small>
    </td>
   </tr>
  
   <tr><td><table></table></td></tr>
   <tr><td><table></table></td></tr>
  
   <tr>
    <td bgcolor="#EEEEEE"><small><em>Groupings</em></small></td>
   </tr> 
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Category</b></small></td>
    <td>
     <select name="category" size="1">''')
    for category in categories:
        wfile.write('''
      <option value="%s">%s</option>''' % (category, category))
    wfile.write('''
     </select>
    </td>
    <td>
     <small>&nbsp;(regex</small>
     <input type="text" name="category_regex"/>
     <small>)</small>
    </td>
    <td bgcolor="#FFFFFF">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" name="category_column" value="on">Show column
      </input>
     </label></small>
    </td>

   </tr>
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Configuration</b></small></td>
    <td>
     <select name="configuration" size="1">''')
    for configuration in configurations:
        wfile.write('''
      <option value="%s">%s</option>''' % (configuration,
                                           configuration))
    wfile.write('''
     </select>
    </td>
    <td>
     <small>&nbsp;(regex</small>
     <input type="text" name="configuration_regex"/>
     <small>)</small>
    </td>
    <td bgcolor="#FFFFFF">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" name="configuration_column" value="on">Show column
      </input>
     </label></small>
    </td>

   </tr>
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Keyword</b></small></td>
    <td>
     <select name="keyword" size="1">''')
    for keyword in keywords:
        wfile.write('''
      <option value="%s">%s</option>''' % (keyword,
                                           keyword))
    wfile.write('''
     </select>
    </td>
    <td>
     <small>&nbsp;(regex</small>
     <input type="text" name="keyword_regex"/>
     <small>)</small>
    </td>
    <td bgcolor="#FFFFFF">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" name="keyword_column" value="on">Show column
      </input>
     </label></small>
    </td>

   </tr>
 
   <tr><td><table></table></td></tr>
   <tr><td><table></table></td></tr>
  
   <tr>
    <td bgcolor="#EEEEEE"><small><em>Versions</em></small></td>
   </tr> 
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Reported in</b></small></td>
    <td>
     <select name="reported_in" size="1">''')
    for version in versions:
        wfile.write('''
         <option value="%s">%s</option>''' % (version, version))
    wfile.write('''
     </select>
    </td>
    <td>
     <small>&nbsp;(regex</small>
     <input type="text" name="reported_in_regex"/>
     <small>)</small>
    </td>
    <td bgcolor="#FFFFFF">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" name="reported_in_column" value="on">Show column
      </input>
     </label></small>
    </td>
   </tr>
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Fixed in</b></small></td>
    <td>
     <select name="fixed_in" size="1">''')
    for version in versions:
        wfile.write('''
         <option value="%s">%s</option>''' % (version, version))
    wfile.write('''
     </select>
    </td>
    <td>
     <small>&nbsp;(regex</small>
     <input type="text" name="fixed_in_regex"/>
     <small>)</small>
    </td>
    <td bgcolor="#FFFFFF">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" name="fixed_in_column" value="on">Show column
      </input>
     </label></small>
    </td>
   </tr>
   <tr bgcolor="#DDDDDD">
    <td><small><b>&nbsp;&nbsp;Tested ok in</b></small></td>
    <td>
     <select name="tested_ok_in" size="1">
     ''')
    for version in versions:
        wfile.write('''
         <option value="%s">%s</option>''' % (version, version))
    wfile.write('''
     </select>
    </td>
    <td>
     <small>&nbsp;(regex</small>
     <input type="text" name="tested_ok_in_regex"/>
     <small>)</small>
    </td>
    <td bgcolor="#FFFFFF">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" name="tested_ok_in_column" value="on">Show column
      </input>
     </label></small>
    </td>
   </tr>

   <tr><td><table></table></td></tr>
   <tr><td><table></table></td></tr>
  
   <tr>
    <td colspan="5" align="right">
     <input type="submit" value="Submit"/>
    </td>
   </tr>
  </table>
  </form>
  </blockquote></center>
''')
