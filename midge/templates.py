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
    text = "\n<br/>\n".join(rows)

    for name, pattern, substitute in config.CommentMappings.mappings:
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
  <link rel="stylesheet" type="text/css" href="default.css"/>
  <script>
  <!--
  function set_focus() {
     for (i=0; i<document.forms.length; i++) {
        form = document.forms[i]
        if (form.name == "mainform") {
             form.elements[0].focus();
             break;
        }
    }
  }
  // -->
  </script>
 </head>
 <body onLoad="set_focus()">
  <form action="view">
   <table id="header">
    <tr>
     <td id="headerTitle">
     Midge
     </td>
     <td id="projectName">
      Project: <b>%(project)s</b>
     </td>
    </tr>
   </table>
   <table id="banner">
    <tr>
     <td align="left">
      <a href="home">Home</a> &middot;
      <a href="new">Add new bug</a> &middot;
      <a href="list">List bugs</a> &middot; 
      <a href="search">Search bugs</a> &middot; 
        Find bug <input size="5" name="bug_id" type="text"/>
      <input type="submit" value="Go"/>
     </td>
     <td align="right">
      <a href="help">Help</a>
     </td>
    </tr>
   </table>
  </form>
  <div id="body">
''' % {"title": title, "project":config.Project.name})

def vspace(wfile):
    wfile.write("<br/>")

def hrule(wfile):
    wfile.write("<hr/>")

def title(wfile, title):
    wfile.write('<h1>%s</h1>' % title)
        
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
  </div>
  <p></p>
  <table id="footer">
   <tr>
    <td align="left">
     <em>Version %(version)s.</em>
     See <a href="http://midge.sourceforge.net">
     http://midge.sourceforge.net</a> for updates.
    </td>
    <td align="right">
     Copyright &copy; 2004, Timothy Corbett-Clark.
    </td>
   </tr>
  </table>
 </body>
</html>''' % {"version": get_version()})


def login_form(wfile, path, usernames):
    wfile.write('''
   <form name="mainform" action="%s" method="POST">
    <table class="centered" cellpadding="5" cellspacing="0" border="0">
     <tr class="form">
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
     <tr class="form">
      <td valign="baseline"><small><b>Password</b></small></td>
      <td>
       <input type="password" name="password"/>
      </td>
     </tr>
     <tr><td><table></table></td></tr>
     <tr>
      <td colspan="3" align="right">
       <input type="submit" value="Login"/>
      </td>
     </tr>
    </table>
   </form>''')


def add_user_form(wfile, path):
    wfile.write('''
   <form name="mainform" action="%(path)s" method="POST">
    <table class="centered" cellpadding="5" cellspacing="0" border="0">
     <tr class="form">
      <td valign="baseline"><small><b>Username</b></small></td>
      <td>
       <input type="text" size="40" name="username"/>
      </td>
     </tr>
     <tr class="form">
      <td valign="baseline"><small><b>Name</b></small></td>
      <td>
       <input type="text" size="40" name="name"/>
      </td>
     </tr>
     <tr class="form">
      <td valign="baseline"><small><b>Email</b></small></td>
      <td>
       <input type="text" size="40" name="email"/>
      </td>
     </tr>
     <tr class="form">
      <td valign="baseline"><small><b>Password</b></small></td>
      <td>
       <input type="password" size="40" name="password"/>
      </td>
     </tr>
     <tr class="form">
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
   </form>''' % {"path": path})


def modify_user_form(wfile, path, name, email):
    wfile.write('''
   <form name="mainform" action="%(path)s" method="POST">
    <table class="centered" cellpadding="5" cellspacing="0" border="0">
     <tr class="form">
      <td valign="baseline"><small><b>Name</b></small></td>
      <td>
       <input type="text" size="40" name="name" value="%(name)s"/>
      </td>
     </tr>
     <tr class="form">
      <td valign="baseline"><small><b>Email</b></small></td>
      <td>
       <input type="text" size="40" name="email" value="%(email)s"/>
      </td>
     </tr>
     <tr class="form">
      <td valign="baseline"><small><b>Existing Password</b></small></td>
      <td>
       <input type="password" size="40" name="password"/>
      </td>
     </tr>

     <tr><td><table></table></td></tr>
      
     <tr class="form">
      <td valign="baseline"><small><b>New password</b></small></td>
      <td>
       <input type="password" size="40" name="new_password"/>
      </td>
     </tr>
     <tr class="form">
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
   </form>''' % {"path": path, "name": name, "email": email})


def new_bug_form(wfile, path, versions, categories):
    wfile.write('''
   <form name="mainform" action="%(path)s" method="POST">
    <table class="centered" cellpadding="5" cellspacing="0" border="0">
     <tr class="form">
      <td class="form-row-heading" valign="baseline">Title</td>
      <td colspan="3">
       <input class="expand" type="text" maxlength="60" name="title"/>
      </td>
     </tr>
     <tr class="form">
      <td class="form-row-heading" valign="baseline">Version</td>
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
     <tr class="form">
      <td class="form-row-heading" valign="baseline">Category</td>
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

     <tr class="form">
      <td class="form-row-heading" valign="baseline">Description</td>
      <td colspan="3">
       <textarea class="expand" name="description" rows="8"></textarea>
      </td>
     </tr>
     <tr><td><table></table></td></tr>
     <tr>
      <td colspan="3" align="right">
       <input type="submit" value="Submit"/>
      </td>
     </tr>
    </table>
   </form>''')


class StatusHints(object):

    new = ("(set to <b>scheduled</b> to fix now, or "
           "<b>reviewed</b> to fix later)")

    reviewed = "(set to <b>scheduled</b> to have this bug fixed now)"

    scheduled = "(set to <b>fixed</b> once ready for testing)"

    fixed = ("(set to <b>closed</b> once confirmed fixed, or "
             "<b>new</b> if still broken)")

    closed = ""


def show_comments(wfile, bug):
    for comment in bug.comments:
        wfile.write('''
  <table class="comments-heading"">
   <tr>
    <td>
     Posted by <b>%(name)s</b> (%(username)s) on
               <b>%(date)s</b> at
               <b>%(time)s</b>
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
    if bug.resolution:
        resolution = " (%s)" % bug.resolution
    else:
        resolution = ""
    if bug.priority:
        priority = ", priority %s" % bug.priority
    else:
        priority = ""
    wfile.write('''
  <p>
   <strong>Bug %(bug_id)s, %(status)s%(resolution)s%(priority)s</strong>
   (<a href="#editbugform">more</a>)
  </p>''' % {"bug_id": bug.bug_id,
             "status": bug.status,
             "resolution": resolution,
             "priority": priority})
 
    
def edit_bug_form(wfile, path, bug,
                  statuses, priorities, resolutions,
                  categories, keywords, versions):
    wfile.write('''
  <br/>
  <a name="editbugform" id="editbugform"></a>
  <form name="mainform" action="%(path)s" method="POST">
  <input type="hidden" name="bug_id" value="%(bug_id)s"/>
  <table class="centered" cellpadding="3" cellspacing="0" border="0">
   <tr>
    <td class="form-tab">States</td>
   </tr> 
   <tr class="form">
    <td class="form-row-heading">Status</td>
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
   <tr class="form">
    <td class="form-row-heading">Priority</td>
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
   <tr class="form">
    <td class="form-row-heading">Resolution</td>
    <td>
     <select name="resolution" size="1">''')
    for resolution in resolutions:
        if bug.resolution == resolution:
            wfile.write('''
      <option value="%s" selected="selected">%s</option>''' % (resolution, resolution))
        else:
            wfile.write('''
      <option value="%s">%s</option>''' % (resolution, resolution))
    wfile.write('''
     </select>
    </td>
    <td align="right"><small>(or use a new resolution</small>
        <input type="text" name="new_resolution"></input><small>)</small>
    </td>
   </tr>
  
   <tr><td><table></table></td></tr>
   <tr><td><table></table></td></tr>
  
   <tr>
    <td class="form-tab">Groupings</td>
   </tr> 
   <tr class="form">
    <td class="form-row-heading">Category</td>
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
   <tr class="form">
    <td class="form-row-heading">Keyword</td>
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
    <td class="form-tab">Versions</td>
   </tr> 
   <tr class="form">
    <td class="form-row-heading">Reported in</td>
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
   <tr class="form">
    <td class="form-row-heading">Fixed in</td>
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
   <tr class="form">
    <td class="form-row-heading">Tested ok in</td>
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
    <td class="form-tab">Add comment</td>
   </tr> 
   <tr class="form">
    <td colspan="3">
     <textarea class="expand" name="comment" rows="8"></textarea>
    </td>
   </tr>
  
   <tr><td><table></table></td></tr>
  
   <tr>
    <td colspan="3" align="right">
     <input type="submit" value="Submit"/>
    </td>
   </tr>
  </table>
  </form>''')
  

def list_form(wfile, path, status_counts):
    wfile.write('''
   <form name="mainform" action="%(path)s">
    <table class="centered" cellpadding="3" cellspacing="0" border="0">
     <tr class="form">
      <td>
       <input type="radio" name="status" value="new" checked="checked"/>
       %(n_new)s
      </td>
      <td>new</td>
     </tr>
     <tr class="form">
      <td>
       <input type="radio" name="status" value="reviewed"/>
       %(n_reviewed)s
      </td>
      <td>reviewed</td>
     </tr>
     <tr class="form">
      <td>
       <input type="radio" name="status" value="scheduled"/>
       %(n_scheduled)s
      </td>
      <td>scheduled</td>
     </tr>
     <tr class="form">
      <td>
       <input type="radio" name="status" value="fixed"/>
       %(n_fixed)s
      </td>
      <td>fixed</td>
     </tr>
     <tr class="form">
      <td>
       <input type="radio" name="status" value="closed"/>
       %(n_closed)s
      </td>
      <td>closed</td>
     </tr>

     <tr><td><table></table></td></tr>
     <tr><td><table></table></td></tr>
     
     <tr align="right" class="white">
      <td colspan="2" align="right">
       <input type="submit" value="List bugs"/>
      </td>
     </tr>
    </table>
   </form>''' %
                {"path": path,
                 "n_new": status_counts.new,
                 "n_reviewed": status_counts.reviewed,
                 "n_scheduled": status_counts.scheduled,
                 "n_fixed": status_counts.fixed,
                 "n_closed": status_counts.closed})


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
            css_class = "last-column-heading"
        else:
            css_class = "column-heading"
        wfile.write('''
     <th class="%(css_class)s">
      <a href="%(url)s">
       %(heading)s
      </a>''' % {"heading": heading,
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
    styles = ("odd-row", "even-row")
    row_index = 0
    for row in rows:
        row_index += 1
        wfile.write('''
    <tr class="row">''')
        for variable, value in row.get():
            if variable == "bug_id":
                value = '<a href="/view?bug_id=%(bug_id)s">%(bug_id)s</a>' % \
                        {"bug_id": value}
            if variable == "title":
                style = styles[row_index % 2] + "-last"
            else:
                style = styles[row_index % 2] + "-not-last"
            wfile.write('''
     <td class="%(style)s">
      %(value)s
     </td>
  ''' % {"style": style,
         "value": value})
        wfile.write('''
    </tr>''') 

def table_of_bugs(wfile, path, search):
    assert len(search.rows) > 0
    titles = search.titles
    variables = search.variables
    sorted_by = search.sort_by
    ordered = search.order
    wfile.write('''
   <table class="list-of-bugs">
    <thead>''')
    _table_headings(wfile, path, titles,
                    variables, sorted_by, ordered)
    wfile.write('''
    </thead>
    <tbody>''')
    _table_rows(wfile, search.rows)
    wfile.write('''
    </tbody>
   </table>''')


def search_form(wfile, path, values,
                statuses, priorities, resolutions,
                categories, keywords, versions):
    wfile.write('''
  <form name="mainform" action="%(path)s">
  <table class="centered" cellpadding="3" cellspacing="0" border="0">
   <tr>
    <td class="form-tab">Text</td>
   </tr> 
   <tr class="form">
    <td class="form-row-heading">Title</td>
    <td>
     <input name="title" value="%(title)s" type="text"/>
    </td>
   </tr>
   <tr class="form">
    <td class="form-row-heading">Comments</td>
    <td>
     <input name="comments" value="%(comments)s" type="text"/>
    </td>
   </tr>

   <tr><td><table></table></td></tr>
   <tr><td><table></table></td></tr>
  
   <tr>
    <td class="form-tab">States</td>
   </tr> 
   <tr class="form">
    <td class="form-row-heading">Status</td>
    <td>
     <select name="status" size="1">''' % {"path": path,
                                           "title": values.get("title", ""),
                                           "comments": values.get("comments", "")})
    for status in statuses:
        if values.get("status", None) == status:
            wfile.write('''
      <option value="%s" selected="selected">%s</option>''' % (status, status))
        else:
            wfile.write('''
      <option value="%s">%s</option>''' % (status, status))
    if values.get("status_column", None):
        checked = 'checked="yes"'
    else:
        checked = ""        
    wfile.write('''
     </select>
    </td>
    <td>
     <small>&nbsp;(regex</small>
     <input type="text" value="%(status_regex)s" name="status_regex"/>
     <small>)</small>
    </td>
    <td class="white">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" %(checked)s name="status_column" value="on">Show column
      </input>
     </label></small>
    </td>
   </tr>
   <tr class="form">
    <td class="form-row-heading">Priority</td>
    <td>
     <select name="priority" size="1">''' % \
                {"status_regex": values.get("status_regex", ""),
                 "checked": checked})
    for priority in priorities:
        if values.get("priority", None) == priority:
            wfile.write('''
      <option value="%s" selected="selected">%s</option>''' % (priority, priority))
        else:
            wfile.write('''
      <option value="%s">%s</option>''' % (priority, priority))
    if values.get("priority_column", None):
        checked = 'checked="yes"'
    else:
        checked = ""        
    wfile.write('''
     </select>
    </td>
    <td>
     <small>&nbsp;(regex</small>
     <input type="text" value="%(priority_regex)s" name="priority_regex"/>
     <small>)</small>
    </td>
    <td class="white">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" %(checked)s name="priority_column" value="on">Show column
      </input>
     </label></small>
    </td>
   </tr>
   <tr class="form">
    <td class="form-row-heading">Resolution</td>
    <td>
     <select name="resolution" size="1">''' % \
                {"priority_regex": values.get("priority_regex", ""),
                 "checked": checked})


    for resolution in resolutions:
        wfile.write('''
      <option value="%s">%s</option>''' % (resolution, resolution))
    wfile.write('''
     </select>
    </td>
    <td>
     <small>&nbsp;(regex</small>
     <input type="text" name="resolution_regex"/>
     <small>)</small>
    </td>
    <td class="white">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" name="resolution_column" value="on">Show column
      </input>
     </label></small>
    </td>
   </tr>
  
   <tr><td><table></table></td></tr>
   <tr><td><table></table></td></tr>
  
   <tr>
    <td class="form-tab">Groupings</td>
   </tr> 
   <tr class="form">
    <td class="form-row-heading">Category</td>
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
    <td class="white">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" name="category_column" value="on">Show column
      </input>
     </label></small>
    </td>
   </tr>

   <tr class="form">
    <td class="form-row-heading">Keyword</td>
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
    <td class="white">&nbsp;</td>
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
    <td class="form-tab">Versions</td>
   </tr> 
   <tr class="form">
    <td class="form-row-heading">Reported in</td>
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
    <td class="white">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" name="reported_in_column" value="on">Show column
      </input>
     </label></small>
    </td>
   </tr>
   <tr class="form">
    <td class="form-row-heading">Fixed in</td>
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
    <td class="white">&nbsp;</td>
    <td>
     <small><label>
      <input type="checkbox" name="fixed_in_column" value="on">Show column
      </input>
     </label></small>
    </td>
   </tr>
   <tr class="form">
    <td class="form-row-heading">Tested ok in</td>
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
    <td class="white">&nbsp;</td>
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
 </form>''')
