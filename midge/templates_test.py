# $Id$
# (C) Timothy Corbett-Clark, 2004

"""Unittests for the template module."""

import cStringIO
import mx.DateTime
import unittest
import xml.sax

import midge.templates as templates


class TemplatesTestException(Exception):

    pass


class Handler(xml.sax.handler.ContentHandler):

    pass

class ErrorHandler(xml.sax.handler.ErrorHandler):

    def fatalError(self, e):
        if isinstance(e, xml.sax.SAXParseException):
            raise TemplatesTestException, "%s on line %d, column %d" % (
                e.getMessage(), e.getLineNumber()-1, e.getColumnNumber())


class TemplatesTests(unittest.TestCase):

    def get_wfile(self, string=None):
        wfile = cStringIO.StringIO()
        if string:
            wfile.write(string)
        return wfile
            
    def is_well_formed(self, wfile):
        wfile.reset()
        s = wfile.getvalue()
        s = s.replace("&copy;", "(c)")
        s = s.replace("&nbsp;", " ")
        s = s.replace("&middot;", "|")
        wfile = self.get_wfile(s)
        wfile.reset()
        try:
            xml.sax.parse(wfile, Handler(), ErrorHandler())
            return True
        except TemplatesTestException, e:
            print e
            lines = wfile.getvalue().split("\n")
            for line_number, line in enumerate(lines):
                print "%4d %s" % (line_number, line)
            return False

    def test_format_comment(self):
        """Check format comment"""
        self.assertEqual("foobar", templates.format_comment("\nfoobar"))
        self.assertEqual("foobar", templates.format_comment("foobar"))
        self.assertEqual("foo\n<br/>\nbar", templates.format_comment("foo\nbar"))
        self.assertEqual("&nbsp;foobar", templates.format_comment(" foobar"))
        self.assertEqual("&nbsp;&nbsp;foo", templates.format_comment("  foo"))

    def test_hrule(self):
        """Check hrule"""
        wfile = self.get_wfile()
        templates.hrule(wfile)
        self.assert_(self.is_well_formed(wfile))

    def test_header(self):
        """Check header"""
        wfile = self.get_wfile()
        templates.header(wfile)
        wfile.write("</div></body></html>")
        self.assert_(self.is_well_formed(wfile))

        wfile = self.get_wfile()
        templates.header(wfile, "extra title")
        wfile.write("</div></body></html>")
        self.assert_(self.is_well_formed(wfile))

    def test_title(self):
        """Check title"""
        wfile = self.get_wfile()
        wfile.write("<body>")
        templates.title(wfile, "a title")
        wfile.write("</body>")
        self.assert_(self.is_well_formed(wfile))

    def test_paragraph(self):
        """Check paragraph"""
        wfile = self.get_wfile()
        templates.paragraph(wfile, "a paragraph")
        self.assert_(self.is_well_formed(wfile))
        
    def test_bullets(self):
        """Check bullets"""
        wfile = self.get_wfile()
        templates.bullets(wfile, ["item1", "item2"])
        self.assert_(self.is_well_formed(wfile))
        
    def test_footer(self):
        """Check footer"""
        wfile = self.get_wfile()
        wfile.write("<html>\n")
        wfile.write(" <body>\n")
        wfile.write("  <div>\n")
        templates.footer(wfile)
        self.assert_(self.is_well_formed(wfile))
        
    def test_possible_actions(self):
        """Check possible actions"""
        wfile = self.get_wfile()
        templates.possible_actions(wfile, [("href1", "label1"),
                                  ("href2", "label2")])
        self.assert_(self.is_well_formed(wfile))

    def test_login_form(self):
        """Check login form"""
        wfile = self.get_wfile()
        templates.login_form(wfile, "a path", ["user1", "user2"])
        self.assert_(self.is_well_formed(wfile))

    def test_add_user_form(self):
        """Check add user form"""
        wfile = self.get_wfile()
        templates.add_user_form(wfile, "a path")
        self.assert_(self.is_well_formed(wfile))

    def test_modify_user_form(self):
        """Check modify user form"""
        wfile = self.get_wfile()
        templates.modify_user_form(wfile, "a path", "a name", "an email")
        self.assert_(self.is_well_formed(wfile))

    def test_new_bug_form(self):
        """Check new bug form"""
        wfile = self.get_wfile()
        templates.new_bug_form(wfile,
                               "a path",
                               ["version1", "version2"],
                               ["category1", "category2"],
                               ["keyword1", "keyword2"])
        self.assert_(self.is_well_formed(wfile))

    def test_edit_bug_form(self):
        """Check edit bug form"""
        class MockComment:
            users_name = "my name"
            username = "my username"
            date = mx.DateTime.now()
            text = "this is a comment"

        class MockBug:
            bug_id = 3
            status = "new"
            priority = "priority1"
            resolution = "resolution1"
            category = "category1"
            keyword = "keyword1"
            reported_in = "version2"
            fixed_in = "version2"
            tested_ok_in = "version2"
            comments = [MockComment(), MockComment()]

        wfile = self.get_wfile()
        wfile.write("<test>\n")
        templates.edit_bug_form(wfile,
                                "a path",
                                MockBug(),
                                ["status1", "status2"],
                                ["priority1", "priority2"],
                                ["resolution1", "resolution2"],
                                ["category1", "category2"],
                                ["keyword1", "keyword2"],
                                ["version1", "version2"])
        wfile.write("</test>")
        self.assert_(self.is_well_formed(wfile))

    def test_bug_status_summary(self):
        """Check bug status summary"""
        class MockComment:
            users_name = "my name"
            username = "my username"
            date = mx.DateTime.now()
            text = "this is a comment"

        class MockBug:
            bug_id = 3
            title = "whatever"
            status = "new"
            priority = "priority1"
            resolution = "resolution1"
            category = "category1"
            keyword = "keyword1"
            reported_in = "version2"
            fixed_in = "version2"
            tested_ok_in = "version2"
            comments = [MockComment(), MockComment()]

        wfile = self.get_wfile()
        wfile.write("<test>\n")
        templates.bug_status_summary(wfile, MockBug())
        wfile.write("</test>")
        self.assert_(self.is_well_formed(wfile))

    def test_list_form(self):
        """Check list form"""
        class MockStatusCounts:
            new = 3
            reviewed = 45
            scheduled = 12
            fixed = 0
            closed = 4534
        
        wfile = self.get_wfile()
        wfile.write("<test>\n")
        templates.list_form(wfile, "a path", MockStatusCounts())
        wfile.write("</test>")
        self.assert_(self.is_well_formed(wfile))

    def test_table_headings(self):
        """Check table headings"""
        wfile = self.get_wfile()
        templates._table_headings(wfile,
                                  ["title1", "title"],
                                  ["variable1", "variable"])
        self.assert_(self.is_well_formed(wfile))

    def test_sortable_table_headings(self):
        """Check sortable table headings"""
        wfile = self.get_wfile()
        templates._sortable_table_headings(wfile,
                                           "a path",
                                           ["title1", "title"],
                                           ["variable1", "variable"],
                                           "variable2",
                                           "ascending")
        self.assert_(self.is_well_formed(wfile))

    def test_table_rows(self):
        """Check table rows"""
        class MockRow:
            
            bug_id = "334"
            
            def get(self):
                return [("variable1", "value1"), ("variable2", "value2")]

        wfile = self.get_wfile()
        wfile.write("<test>\n")
        templates._table_rows(wfile, [MockRow(), MockRow()])
        wfile.write("</test>")
        self.assert_(self.is_well_formed(wfile))

    def test_table_of_bugs(self):
        """Check table of bugs"""
        class MockRow:
            
            bug_id = "334"

            status = "new"
            titles = ["title1", "title2"]
            variables = ["variable1", "variable2"]
            sorted_by = "variable2"
            ordered = "descending"
            
            def get(self):
                return [("variable1", "value1"), ("variable2", "value2")]
            
        wfile = self.get_wfile()
        templates.table_of_bugs(wfile, "a path", [MockRow()])
        self.assert_(self.is_well_formed(wfile))
        
    def test_table_of_bugs(self):
        """Check search for bugs"""
        wfile = self.get_wfile()
        templates.search_form(wfile, "a path", {},
                              ["a status"],
                              ["a priority"],
                              ["a resolution"],
                              ["a category"],
                              ["a keyword"],
                              ["a version"])
        self.assert_(self.is_well_formed(wfile))
        
    def test_changes_table(self):
        """Check table of changes"""

        class MockRow:
            
            bug_id = "334"

            status = "new"
            titles = ["title1", "title2"]
            variables = ["variable1", "variable2"]
            sorted_by = "variable2"
            ordered = "descending"
            
            def get(self):
                return [("variable1", "value1"), ("variable2", "value2")]
            
        class MockRecentChanges:

            variables = "bug_id", "username", "date", "description"
            titles = "Bug", "User", "Date", "Description"
            sort_by = "date"
            order = "ascending"
            rows = [MockRow(), MockRow()]
        
        wfile = self.get_wfile()
        templates.table_of_changes(wfile, "a path", MockRecentChanges())
        self.assert_(self.is_well_formed(wfile))
        
