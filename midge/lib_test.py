# $Id$
# (C) Timothy Corbett-Clark, 2004

import unittest

import midge.lib


class LibTests(unittest.TestCase):

    def test_html_entity_escape(self):
        """Check html entity escape"""
        self.assertEqual(midge.lib.html_entity_escape("&"), "&amp;")
        self.assertEqual(midge.lib.html_entity_escape("<"), "&lt;")
        self.assertEqual(midge.lib.html_entity_escape(">"), "&gt;")
        self.assertEqual(midge.lib.html_entity_escape("&&"), "&amp;&amp;")
        self.assertEqual(midge.lib.html_entity_escape("&<"), "&amp;&lt;")
        self.assertEqual(midge.lib.html_entity_escape("<&"), "&lt;&amp;")

    def test_join_and_split_url(self):
        """Check join and split url"""

        url_splits = [("a/b", {"x":"foo"}, "a/b?x=foo"),
                      ("a/b", {"x":"foo bar"}, "a/b?x=foo+bar"),
                      ("a/b", {"x":"foo", "y":"bar"}, "a/b?y=bar&x=foo")]
        
        for base, params, url in url_splits:
            self.assertEqual(midge.lib.join_url(base, params), url)
            self.assertEqual(midge.lib.split_url(url), (base, params))
