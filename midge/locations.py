# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Set of classes to manage URL locations, such as /list and /login."""

import os.path

import midge.application as application
import midge.config as config
import midge.lib as lib
import midge.server as server
import midge.templates as templates


class Location:

    """Every Location corresponds to a URL (without any arguments).

    All Locations share the same instance of the application.

    """

    def __init__(self, application):
        self.application = application

    def handle_post(self, session_id, values, post_data, wfile):
        wfile.write("TODO: implement this post (in subclass %s)" %
                    self.__class__.__name__)

    def handle_get(self, session_id, values, wfile):
        wfile.write("TODO: implement this get (in subclass %s)" %
                    self.__class__.__name__)

    def redirect(self, location, next_location=None):
        """Effect an http redirect to a new location."""
        if next_location:
            url = lib.join_url(location, {"next": next_location})
        else:
            url = location
        raise server.RedirectException, url


class Home(Location):

    path = "/home"

    def handle_get(self, session_id, values, wfile):
        user = self.application.get_user(session_id)
        if user:
            templates.header(wfile)
            templates.title(wfile, "Home")
            templates.paragraph(
                wfile,
                'You are logged in as '
                '<b>%s</b> with a username of <b>%s</b>.' %
                (user.name, user.username))
            templates.paragraph(
                wfile,
                "You will be automatically logged-out after "
                "any (long) period of inactivity.")
            templates.possible_actions(wfile,
                                       ("logout", "Logout"),
                                       ("modifyuser", "Modify user account"))
            templates.footer(wfile)
        else:
            templates.header(wfile)
            templates.title(wfile, "Home")
            templates.paragraph(
                wfile,
                "Either login with an existing username, "
                "or create a new account if you are a new user.")
            templates.possible_actions(wfile,
                                       ("login", "Login"),
                                       ("adduser",
                                        "Create a new user account"))
            templates.footer(wfile)


class Root(Home):

    path = "/"
            

class Logout(Location):

    path = "/logout"

    def handle_get(self, session_id, values, wfile):
        user = self.application.get_user(session_id)
        if user:
            self.application.logout(session_id)
            self.redirect(Home.path)
        else:
            templates.header(wfile)
            templates.title(wfile, "You were not logged-in!")
            templates.paragraph(
                wfile,
                "If you wish, you can go to the main screen "
                "in order to log in as a new user.")
            templates.possible_actions(wfile, ("home", "Home"))
            templates.footer(wfile)


class Login(Location):

    path = "/login"

    def handle_get(self, session_id, values, wfile):
        if "next" not in values:
            values["next"] = Home.path
        user = self.application.get_user(session_id)
        templates.header(wfile)
        templates.title(wfile, "User login")
        if user:
            templates.paragraph(
                wfile,
                'Note that you are already logged in as '
                '<b>%s</b> with a username of <b>%s</b>.' %
                (user.name, user.username))
            templates.paragraph(
                wfile,
                'To change user, enter a new username and password and click '
                'the "Login" button.')
            templates.login_form(wfile, self.path, self.application.usernames)
        else:
            path = lib.join_url(self.path, values)
            templates.paragraph(
                wfile,
                'If you have not yet created a user account, '
                'do so now.')
            templates.possible_actions(wfile,
                                       ("adduser", "Create new account"))
            templates.login_form(wfile, path, self.application.usernames)
        templates.footer(wfile)

    def handle_post(self, session_id, values, post_data, wfile):
        next_location = values.pop("next", None) or Home.path
        username = post_data.get("username", None)
        password = post_data.get("password", None)
        if username and password and \
               self.application.login(session_id, username, password):
            path = lib.join_url(next_location, values)
            self.redirect(path)
        else:
            user = self.application.get_user(session_id)
            templates.header(wfile)
            templates.title(wfile, "Login failed!")
            if username:
                templates.paragraph(
                    wfile,
                    "You entered an incorrect password for user of username "
                    "<b>%s</b>." % username)
                templates.paragraph(
                    wfile,
                    "Use the back-button of your browser to try again, "
                    "or click below to request that your password be emailed "
                    "to you.")
                templates.possible_actions(
                    wfile,
                    ("emailpassword?username=%s" % username, 
                     "Email me my password"))
            else:
                templates.paragraph(
                    wfile,
                    "You did not provide a username. "
                    "Use the back-button of your browser to try again.")
            templates.footer(wfile)


class EmailPassword(Location):

    path = "/emailpassword"

    def handle_get(self, session_id, values, wfile):
        user = self.application.get_user(session_id)
        username = values.get("username", None)
        templates.header(wfile)
        templates.title(wfile, "Email password")
        if username and self.application.email_password(username):
            templates.paragraph(
                wfile,
                "The password associated with the username "
                "<b>%s</b> " % username +
                "has been sent to the email address for that account.")
        else:
            templates.paragraph(
                wfile,
                "Sorry, your password has not been succesfuly "
                "emailed to you. Either midge is not configured correctly "
                "or your account does not contain a valid email address.")
        templates.footer(wfile)
        

class AddUser(Location):

    path = "/adduser"

    def handle_get(self, session_id, values, wfile):
        user = self.application.get_user(session_id)
        templates.header(wfile)
        templates.title(wfile, "Create a new user account")
        if user:
            templates.paragraph(
                wfile,
                'Note that you are already logged in as '
                '<b>%s</b> with a username of <b>%s</b>.' %
                (user.name, user.username))
            templates.paragraph(
                wfile,
                'It is unlikely that you wish to create a new user account, '
                'as this is normally performed by the new user. '
                'However if you really need to create a new account, '
                'fill in the following form and click the '
                '"Create account" button.')
        else:
            templates.paragraph(
                wfile,
                'If you are sure that you do not already have a user account, '
                'fill in the following form and click the '
                '"Create account" button.')
            templates.paragraph(
                wfile,
                'Note that the Username must be unique, and so you '
                'will not be allowed to create a new account with an existing '
                'Username.')
        templates.add_user_form(wfile, self.path)
        templates.footer(wfile)
        
    def handle_post(self, session_id, values, post_data, wfile):
        user = self.application.get_user(session_id)
        
        username = post_data.get("username", None)
        name = post_data.get("name", None)
        email = post_data.get("email", None)
        password = post_data.get("password", None)
        password_again = post_data.get("password_again", None)

        templates.header(wfile)

        if username and name and email and password and password_again:
            if password == password_again:
                try:
                    self.application.create_new_user(username,
                                                     name,
                                                     email,
                                                     password)
                    templates.title(wfile, "New user account created ok")
                    templates.paragraph(
                        wfile,
                        "Continue to the login page to use this account.")
                    templates.possible_actions(wfile,
                                               ("login", "Login"))
                except application.ValueInUseException:
                    templates.title(wfile, "Failed to create user account!")
                    templates.paragraph(
                        wfile,
                        "The username you chose (<b>%s</b>) is already in "
                        "use by another user. " % username +
                        "Use the back-button of your browser and try "
                        "a different Username.")
            else:
                templates.title(wfile, "Failed to create user account!")
                templates.paragraph(
                    wfile,
                    "The passwords you provided do not match. "
                    "Use the back-button of your browser to try again.")
        else:
            templates.title(wfile, "Failed to create user account!")
            templates.paragraph(
                wfile,
                "You must provide the following information:")
            problems = [description
                        for (item, description) in ((username, "Username"),
                                                    (name, "Name"),
                                                    (email, "Email"),
                                                    (password, "Password"),
                                                    (password_again,
                                                     "Password (again)"))
                        if not item]
            templates.bullets(wfile, *problems)
            templates.paragraph(
                wfile,
                "Use the back-button of your browser to try again.")
        templates.footer(wfile)


class ModifyUser(Location):

    path = "/modifyuser"

    def handle_get(self, session_id, values, wfile):
        user = self.application.get_user(session_id)
        if user:
            templates.header(wfile)
            templates.title(wfile, 'Modify user account "%s"' % user.username)
            templates.bullets(
                wfile,
                'Supplying a new password is optional.')
            templates.modify_user_form(wfile, self.path, user.name, user.email)
            templates.footer(wfile)
        else:
            self.redirect(Login.path, self.path)
       
    def handle_post(self, session_id, values, post_data, wfile):
        name = post_data.get("name", None)
        email = post_data.get("email", None)
        password = post_data.get("password", None)
        new_password = post_data.get("new_password", None)
        new_password_again = post_data.get("new_password_again", None)
        
        user = self.application.get_user(session_id)
        if user:
            if user.authenticate(password):
                if name:
                    user.name = name
                if email:
                    user.email = email
                templates.header(wfile)
                templates.title(wfile, "User account details changed ok")
                if new_password == new_password_again:
                    if new_password:
                        user.password = new_password
                        templates.paragraph(
                            wfile,
                            "Note that you have changed your "
                            "account to use a <em>new password</em>, "
                            "which must be used from now on.")
                elif new_password or new_password_again:
                    templates.paragraph(
                        wfile,
                        "Note that your password has <em>not</em> "
                        "been changed as the two new passwords you "
                        "provided do not match.")
                templates.paragraph(
                    wfile, "Continue to the home page:")
                templates.possible_actions(wfile, ("/home", "Home"))
            else:
                templates.header(wfile)
                templates.title(wfile, "Failed to change account details!")
                templates.paragraph(
                    wfile,
                    "You failed to authenticate yourself by typing an "
                    "incorrect password. Use the "
                    "back-button of your browser to try again.")
            templates.footer(wfile)
        else:
            self.redirect(Login.path, self.path)


class List(Location):

    path = "/list"

    def handle_get(self, session_id, values, wfile):
        user = self.application.get_user(session_id)
        if user:
            status = values.pop("status", None)
            sort_by = values.pop("sort_by", None)
            order = values.pop("order", None)
            show_method_name = "_show_%s" % status
            if hasattr(self, show_method_name):
                show_method = getattr(self, show_method_name)
                templates.header(wfile)
                show_method(session_id, wfile, sort_by, order)
                templates.footer(wfile)
            else:
                templates.header(wfile)
                templates.title(wfile, "List bugs")
                templates.bullets(
                    wfile,
                    'Each bug list is designed for a particular objective.',
                    'Use the <a href="/search">Search bugs</a> page '
                    'for hand-crafted listings.')
                status_counts = self.application.get_status_counts(session_id)
                templates.list_form(wfile, self.path, status_counts)
                templates.footer(wfile)
        else:
            values["next"] = self.path
            path = lib.join_url(Login.path, values)
            self.redirect(path)

    def _show_new(self, session_id, wfile, sort_by, order):
        if not sort_by:
            sort_by = "category"
        if not order:
            order = "ascending"
        search = application.Search(
            ("bug_id", "category", "reported_in", "title"),
            sort_by, order, status="new")
        self.application.search(session_id, search)
        templates.title(wfile, "All new bugs")
        if search.rows:
            templates.bullets(
                wfile,
                "Bugs that are new and need to be reviewed.")
            url = lib.join_url(self.path, {"status": "new"})
            templates.table_of_bugs(wfile, url, search)
        else:
            templates.paragraph(wfile, "There are no new bugs.")

    def _show_reviewed(self, session_id, wfile, sort_by, order):
        if not sort_by:
            sort_by = "priority"
        if not order:
            order = "descending"
        search = application.Search(
            ("bug_id", "priority", "category", "reported_in", "title"),
            sort_by, order, status="reviewed")
        self.application.search(session_id, search)
        templates.title(wfile, "All reviewed bugs")
        if search.rows:
            templates.bullets(
                wfile,
                "Bugs that are ready to be scheduled "
                "(priority 5 is most important).")
            url = lib.join_url(self.path, {"status": "reviewed"})
            templates.table_of_bugs(wfile, url, search)
        else:
            templates.paragraph(wfile,
                                "There are no bugs in the reviewed state.")

    def _show_scheduled(self, session_id, wfile, sort_by, order):
        if not sort_by:
            sort_by = "priority"
        if not order:
            order = "descending"
        search = application.Search(
            ("bug_id", "priority", "category", "reported_in", "title"),
            sort_by, order, status="scheduled")
        self.application.search(session_id, search)
        templates.title(wfile, "All scheduled bugs")
        if search.rows:
            templates.bullets(
                wfile,
                "Bugs that are ready to be fixed "
                "(starting with priority 5).")
            url = lib.join_url(self.path, {"status": "scheduled"})
            templates.table_of_bugs(wfile, url, search)
        else:
            templates.paragraph(
                wfile,
                "There are no bugs scheduled to be fixed.")

    def _show_fixed(self, session_id, wfile, sort_by, order):
        if not sort_by:
            sort_by = "fixed_in"
        if not order:
            order = "ascending"
        search = application.Search(
            ("bug_id", "priority", "category", "fixed_in", "title"),
            sort_by, order, status="fixed")
        self.application.search(session_id, search)
        templates.title(wfile, "All fixed bugs")
        if search.rows:
            templates.bullets(
                wfile,
                "Bugs that are ready to be tested.")
            url = lib.join_url(self.path, {"status": "fixed"})
            templates.table_of_bugs(wfile, url, search)
        else:
            templates.paragraph(
                wfile,
                "There are no bugs waiting to be tested.")

    def _show_closed(self, session_id, wfile, sort_by, order):
        if not sort_by:
            sort_by = "tested_ok_in"
        if not order:
            order = "ascending"
        search = application.Search(
            ("bug_id", "priority", "category", "tested_ok_in", "title"),
            sort_by, order, status="closed")
        self.application.search(session_id, search)
        templates.title(wfile, "All closed bugs")
        if search.rows:
            url = lib.join_url(self.path, {"status": "closed"})
            templates.table_of_bugs(wfile, url, search)
        else:
            templates.paragraph(wfile,
                                "There are no closed bugs.")

        
class View(Location):

    path = "/view"

    def handle_get(self, session_id, values, wfile):
        user = self.application.get_user(session_id)
        if user:
            bug_id = values.get('bug_id')
            if bug_id:
                templates.header(wfile, "Bug %s" % bug_id)
                try:
                    bug = self.application.get_bug(session_id, bug_id)
                    templates.title(wfile, bug.title)
                    self._show_status_and_comments_and_form(wfile, bug)
                except application.NoSuchBugException:
                    templates.title(wfile, "No such Bug!")
                    templates.paragraph(
                        wfile,
                        'No bug with number = "%s" exists. ' % bug_id)
            else:
                templates.header(wfile)
                templates.title(wfile, "View particular bug")
                templates.paragraph(
                    wfile,
                    'To view a particular bug, enter the bug '
                    'number in the the "Find bug" box and either click '
                    'the "Go" button or press return.')
                templates.paragraph(
                    wfile,
                    '(The "Find bug" box may be found in the header and '
                    'the footer of every page.)')
            templates.footer(wfile)
        else:
            values["next"] = self.path
            path = lib.join_url(Login.path, values)
            self.redirect(path)

    def _show_status_and_comments_and_form(self, wfile, bug):
        templates.bug_status_summary(wfile, bug)
        templates.vspace(wfile)
        templates.show_comments(wfile, bug)
        templates.hrule(wfile)
        templates.edit_bug_form(
            wfile, self.path, bug,
            self.application.statuses,
            self.application.priorities,
            self.application.configurations,
            self.application.categories,
            self.application.keywords,
            self.application.versions)

    def _make_changes(self, session_id, user, post_data, wfile):
        bug_id = post_data.get("bug_id", None)
        old_bug = self.application.get_bug(session_id, bug_id)
        changes = {}

        status = post_data.get("status", None)
        if status != old_bug.status:
            changes["status"] = status

        priority = post_data.get("priority", None)
        if priority != old_bug.priority:
            changes["priority"] = priority

        configuration = post_data.get("configuration", None)
        new_configuration = post_data.get("new_configuration", None)
        if new_configuration:
            configuration = new_configuration
        if configuration != old_bug.configuration:
            changes["configuration"] = configuration            

        category = post_data.get("category", None)
        new_category = post_data.get("new_category", None)
        if new_category:
            category = new_category
        if category != old_bug.category:
            changes["category"] = category

        keyword = post_data.get("keyword", None)
        new_keyword = post_data.get("new_keyword", None)
        if new_keyword:
            keyword = new_keyword
        if keyword != old_bug.keyword:
            changes["keyword"] = keyword

        reported_in = post_data.get("reported_in", None)
        new_reported_in = post_data.get("new_reported_in", None)
        if new_reported_in:
            reported_in = new_reported_in
        if reported_in != old_bug.reported_in:
            changes["reported_in"] = reported_in

        fixed_in = post_data.get("fixed_in", None)
        new_fixed_in = post_data.get("new_fixed_in", None)
        if new_fixed_in:
            fixed_in = new_fixed_in
        if fixed_in != old_bug.fixed_in:
            changes["fixed_in"] = fixed_in

        tested_ok_in = post_data.get("tested_ok_in", None)
        new_tested_ok_in = post_data.get("new_tested_ok_in", None)
        comment = post_data.get("comment", None)
        if new_tested_ok_in:
            tested_ok_in = new_tested_ok_in
        if tested_ok_in != old_bug.tested_ok_in:
            changes["tested_ok_in"] = tested_ok_in

        if comment:
            changes["comment"] = comment
            
        if changes:
            old_bug.change(user, **changes)
        self._report_on_changes(session_id, old_bug, changes, wfile)
        
    def _report_on_changes(self, session_id, old_bug, changes, wfile):
        new_bug = self.application.get_bug(session_id, old_bug.bug_id)
        if changes:
            templates.title(wfile, "Bug update successful")
            bullet_items = []
            if changes.pop("comment", None):
                bullet_items.append("Added new comment.")
            for variable, new_value in changes.iteritems():
                old_value = getattr(old_bug, variable)
                variable = variable.capitalize().replace("_", " ")
                if old_value and new_value:
                    bullet_items.append('Changed "%s" from %s to %s.' % \
                                        (variable, old_value, new_value))
                else:
                    if old_value:
                        bullet_items.append('Unset "%s".' % variable)
                    else:
                        bullet_items.append('Set "%s" to %s.' % \
                                            (variable, new_value))
            templates.bullets(wfile, *bullet_items)
        else:
            templates.title(wfile, "No update needed")
        templates.hrule(wfile)
        templates.title(wfile, new_bug.title)
        self._show_status_and_comments_and_form(wfile, new_bug)

    def handle_post(self, session_id, values, post_data, wfile):
        user = self.application.get_user(session_id)
        if user:
            templates.header(wfile)
            try:
                self._make_changes(session_id, user, post_data, wfile)
            except application.InvalidValueException:
                templates.title(wfile, "Unable to change bug!")
                templates.paragraph(
                    wfile,
                    'One of the new values you have entered is invalid. '
                    'Use the back-button of your browser to correct.')
            templates.footer(wfile)
        else:
            self.redirect(Login.path, lib.join_url(self.path, values))


class New(Location):

    path = "/new"    

    def handle_get(self, session_id, values, wfile):
        user = self.application.get_user(session_id)
        if user:
            templates.header(wfile)
            templates.title(wfile, "Add new bug")
            templates.bullets(
                wfile,
                'Fill in as many fields as possible and '
                'press the "Submit" button.',
                'You must provide at least a title and a description.',
                'Use new values (e.g. for version) if the available ones are unsuitable.')
            templates.new_bug_form(wfile, self.path,
                                   self.application.versions,
                                   self.application.configurations,
                                   self.application.categories)
            templates.footer(wfile)
        else:
            self.redirect(Login.path, self.path)

    def handle_post(self, session_id, values, post_data, wfile):
        user = self.application.get_user(session_id)
        if user:
            templates.header(wfile)
            if self._form_complete(post_data):
                self._add_bug(session_id, wfile, post_data)
            else:
                templates.title(wfile, "Failed to add new bug!")
                templates.paragraph(
                    wfile,
                    "You have not filled in enough fields. "
                    "Use the back-button of your browser to correct this.")
            templates.footer(wfile)
        else:
            self.redirect(Login.path, self.path)

    def _add_bug(self, session_id, wfile, post_data):
        new_version = post_data.pop("new_version", None)
        if new_version:
            post_data["version"] = new_version
        new_configuration = post_data.pop("new_configuration", None)
        if new_configuration:
            post_data["configuration"] = new_configuration
        new_category = post_data.pop("new_category", None)
        if new_category:
            post_data["category"] = new_category

        try:
            bug_id = self.application.add_bug(session_id, **post_data)
            templates.title(wfile, "Successfuly added new bug")
            templates.paragraph(
                wfile,
                'You have justed created new bug, number '
                '%s.' % bug_id)
            templates.possible_actions(
                wfile,
                ("/new", "Add another bug"),
                ("/view?bug_id=%s" % bug_id,
                 "View the newly created Bug %s" % bug_id),
                ("/home", "Home"))
        except application.InvalidValueException:
            templates.title(wfile, "Failed to add new bug!")
            templates.paragraph(
                wfile,
                'One of the new values you have entered is invalid. '
                'Use the back-button of your browser to correct.')

    def _form_complete(self, post_data):
        return post_data["title"] and post_data["description"]


class Search(Location):

    path = "/search"    

    def handle_get(self, session_id, values, wfile):
        user = self.application.get_user(session_id)
        if user:
            templates.header(wfile)
            if values:
                self._reload_if_url_can_be_simplified(values)
                self._search(session_id, wfile, values)
            else:
                templates.title(wfile, "Search for bugs")
                templates.bullets(
                    wfile,
                    'All criteria are combined with "And".',
                    'Blank fields are ignored.',
                    'Searches are case insensitive.',
                    'The "regex" fields are for advanced searches '
                    '(and may be ignored).')
                templates.search_form(wfile, self.path,
                            [""] + list(self.application.statuses),
                            self.application.priorities,
                            self.application.configurations,
                            self.application.categories,
                            self.application.keywords,
                            self.application.versions)
            templates.footer(wfile)
        else:
            self.redirect(Login.path, lib.join_url(self.path, values))

    def _reload_if_url_can_be_simplified(self, values):
        new_values = {}
        for k,v in values.iteritems():
            if v:
                new_values[k] = v
        if new_values != values:
            self.redirect(lib.join_url(self.path, new_values))
            
    def _search(self, session_id, wfile, values):
        sort_by = values.pop("sort_by", "bug_id")
        order = values.pop("order", "ascending")

        criteria = {}
        columns = ["bug_id", "title"]
        for key, value in values.items():
            if value:
                if key.endswith("_column"):
                    columns.append(key[:-len("_column")])
                else:
                    criteria[key] = value
        
        search = application.Search(columns, sort_by, order, **criteria)
        try:
            self.application.search(session_id, search)
            templates.title(wfile, "Search result")
            self._pretty_print_search(wfile, criteria)
            if search.rows:
                url = lib.join_url(self.path, values)
                templates.table_of_bugs(wfile, url, search)
            else:
                templates.paragraph(
                    wfile,
                    "No bugs match these criteria!")
        except application.InvalidSearchException, e:
            templates.title(wfile, "Invalid search criteria!")
            templates.paragraph(
                wfile,
                "Use the back-button of your browser "
                "to correct your search.")
            templates.paragraph(
                wfile,
                "Malformed regex expressions are a probable cause. "
                "For example, mismatched parentheses.")

    def _pretty_print_search(self, wfile, criteria):

        def clean_name(s):
            s = s.replace("regex", "(regex)")
            s = s.replace("_", " ")
            return s.capitalize()
        
        bullets = []
        for k,v in criteria.iteritems():
            bullets.append("%s = %s" % (clean_name(k),v))
        templates.bullets(wfile, *bullets)
        
        
class Images(Location):

    path = "/images"    

    def handle_get(self, session_id, values, wfile):
        name = values.get("name", None)
        if name:
            f = file(os.path.join(config.Presentation.directory, "%s" % name))
            wfile.write(f.read())
            f.close()


class DefaultCSS(Location):

    path = "/default.css"

    def handle_get(self, session_id, values, wfile):
        filename = os.path.join(config.Presentation.directory, "default.css")
        f = file(filename)
        wfile.write(f.read())
        f.close()

class Help(Location):

    path = "/help"

    def handle_get(self, session_id, values, wfile):
        templates.header(wfile)
        templates.title(wfile, "Help")
        if config.Project.help:
            templates.bullets(
                wfile,
                'Site-specific help is available '
                '<a href="%s">here.</a>' % config.Project.help)
        else:
            templates.bullets(
                wfile,
                '<em>No site-specific help has been configured.</em>')
        templates.title(wfile, "About")
        templates.paragraph(
            wfile,
            "Midge is a system for tracking bugs found during the "
            "commercial development of a software product. It is "
            "particularly suited to a process for which the filing, "
            "managing, fixing, and testing are all undertaken by "
            "different roles in a trusted environment.")
        templates.paragraph(
            wfile,
            "Midge aims to be consistent, self-explanatory, powerful "
            "enough to efficiently manage thousands of bugs, require no "
            "administration, and be bug-free!")
        templates.paragraph(
            wfile,
            'Midge is released under the terms of the '
            '<a href="http://www.gnu.org/licenses/gpl.txt">'
            'GNU General Public License.</a>')
        templates.paragraph(
            wfile,
            "See <a href=\"http://midge.sourceforge.net\">"
            "http://midge.sourceforge.net</a> for more "
            "information, releases, <em>etc</em>.")
        templates.footer(wfile)
        
