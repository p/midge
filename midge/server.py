# $Id$
# (C) Timothy Corbett-Clark, 2004

"""An HTTP server with session management."""

import BaseHTTPServer
import cStringIO
import random
import select
import sys
import threading
import time
import traceback
import urllib

import midge.config as config
import midge.lib as lib
import midge.logger as logger


class Sessions(object):

    def __init__(self, application):
        self.application = application
        self.session_ids = {}
        self._lock = threading.Lock()

    def acquire_lock(self):
        self._lock.acquire()

    def release_lock(self):
        self._lock.release()

    def _generate_session_id(self):
        session_id = str(random.randint(0, sys.maxint))
        while session_id in self.session_ids:
            session_id = str(random.randint(0, sys.maxint))
        logger.debug("Generating new session: %s" % session_id)
        self._refresh_session(session_id)
        self.application.new_session(session_id)
        return session_id

    def _retire_session(self, session_id):
        try:
            del self.session_ids[session_id]
            logger.debug("Retiring session: %s" % session_id)
            self.application.expired_session(session_id)
        except KeyError:
            pass

    def _retire_expired_sessions(self):
        t0 = time.time()
        for session_id, expire_time in self.session_ids.items():
            if t0 > expire_time:
                self._retire_session(session_id)

    def _refresh_session(self, session_id):
        self.session_ids[session_id] = time.time() + \
                                       60 * config.Server.session_timeout
    
    def get_valid_session_id(self, proposed_session_id):
        self._retire_expired_sessions()
        if proposed_session_id is None:
            valid_session_id = self._generate_session_id()
        elif proposed_session_id in self.session_ids:
            self._refresh_session(proposed_session_id)
            valid_session_id = proposed_session_id
        else:
            valid_session_id = self._generate_session_id()
        return valid_session_id

    def do_maintenance(self):
        self.acquire_lock()
        try:
            logger.info("Scheduled maintenance")
            self.application.do_maintenance()
        finally:
            self.release_lock()


class RedirectException(Exception):

    def __init__(self, path):
        self.path = path
        Exception.__init__(self)
        

class HttpCodes:

    # HTTP 1.1 Protocol: http://www.w3.org/Protocols/rfc2616/rfc2616.html

    OK = 200
    SeeOther = 303
    NotFound = 404
    

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    SERVER_NAME = "midge server"
    SESSION_COOKIE_NAME = "midge_session"

    # The class variables are set by the Server class.
    # Note that the RequestHandler is reinstantiated every GET/POST etc.
    _locations = None
    _sessions = None

    def _send_standard_header(self, session_id):
        self.send_response(HttpCodes.OK)
        self.send_header("Content-type", "text/html")
        self.send_header("Server", self.SERVER_NAME)
        self.send_header("Set-Cookie", "%s=%s" % (self.SESSION_COOKIE_NAME,
                                                  session_id))
        self.end_headers()

    def _send_redirect(self, path):
        logger.debug("Redirect to: %s" % path)
        self.send_response(HttpCodes.SeeOther)
        self.send_header("Content-type", "text/html")
        self.send_header("Server", self.SERVER_NAME)
        self.send_header("Location", path)
        self.end_headers()

    def _send_no_such_location(self, path):
        logger.info("No such location: %s" % path)
        self.send_response(HttpCodes.NotFound)
        self.send_header("Content-type", "text/html")
        self.send_header("Server", self.SERVER_NAME)
        self.end_headers()
        self.wfile.write("<html><body><h1>No such location!</h1>"
                         "<p>The location <b>%s</b> does not exist." % path)
        self.wfile.write(" Perhaps you meant one of the following:<ul>")
        paths = self._locations.keys()
        paths.sort()
        for path in paths:
            self.wfile.write('<li><a href="%s">%s</a></li>' % (path, path))
        self.wfile.write("</ul></body></html>")

    def _send_exception(self):
        lines = logger.get_exception_as_lines()
        for line in lines:
            logger.error(line)
        self.send_response(HttpCodes.OK)
        self.send_header("Content-type", "text/html")
        self.send_header("Server", self.SERVER_NAME)
        self.end_headers()
        self.wfile.write("<html><body><h1>Midge Error!</h1>")
        self.wfile.write("It would appear that Midge is not completely "
                         "free of bugs...")
        self.wfile.write("<blockquote><pre>")
        for line in lines:
            self.wfile.write(line)
            self.wfile.write("\n")
        self.wfile.write("</pre></blockquote></body></html>")

    def _extract_session_id(self):
        cookie = self.headers.get("Cookie", None)
        if cookie is not None:
            for key_value_pairs in cookie.split(";"):
                key, value = key_value_pairs.split("=")
                if key.strip() == self.SESSION_COOKIE_NAME:
                    return value.strip()
        return None

    def _decode_raw_post_data(self, raw_post_data):
        post_data = {}
        for var_pair in raw_post_data.split("&"):
            variable, value = var_pair.split("=")
            post_data[variable] = urllib.unquote_plus(value)
        return post_data

    def do_GET(self):
        self._sessions.acquire_lock()
        try:
            proposed_session_id = self._extract_session_id()
            session_id = self._sessions.get_valid_session_id(
                proposed_session_id)
            path, values = lib.split_url(self.path)
            host = self.client_address[0]
            logger.debug("http get %s from host %s (session %s)" % (path,
                                                                    host,
                                                                    session_id))
            location = self._locations.get(path)
            if location:
                try:
                    wfile = cStringIO.StringIO()
                    location.handle_get(session_id, values, wfile)
                    self._send_standard_header(session_id)
                    self.wfile.write(wfile.getvalue())
                except RedirectException, e:
                    self._send_redirect(e.path)
                except Exception:
                    self._send_exception()
            else:
                self._send_no_such_location(self.path)
        finally:
            self._sessions.release_lock()
        
    def do_POST(self):
        self._sessions.acquire_lock()
        try:
            proposed_session_id = self._extract_session_id()
            session_id = self._sessions.get_valid_session_id(
                proposed_session_id)
            content_length = self.headers.dict.get("content-length", None)
            if content_length is not None:
                raw_post_data = self.rfile.read(int(content_length))
                path, values = lib.split_url(self.path)
                logger.debug(
                    "http post %s for session: %s" % (path, session_id))
                location = self._locations.get(path)
                if location:
                    try:
                        wfile = cStringIO.StringIO()
                        post_data = self._decode_raw_post_data(raw_post_data)
                        location.handle_post(session_id, values,
                                             post_data, wfile)
                        self._send_standard_header(session_id)
                        self.wfile.write(wfile.getvalue())
                    except RedirectException, e:
                        self._send_redirect(e.path)
                    except Exception:
                        self._send_exception()
                else:
                    self._send_no_such_location(self.path)
            else:
                # TODO send an HTTP error code.
                pass
        finally:
            self._sessions.release_lock()

    def log_message(self, *args):
        pass


class Server(object):

    def __init__(self, application, locations):
        self.sessions = Sessions(application)
        RequestHandler._locations = self._get_locations(locations,
                                                        application)
        RequestHandler._sessions = self.sessions
        interface = config.Server.interface
        port = config.Server.port
        if interface:
            logger.info("Creating server on %s:%s" % (interface, port))
        else:
            logger.info("Creating server on all interfaces:%s" % port)
        self.httpd = BaseHTTPServer.HTTPServer( (interface, port),
                                                RequestHandler)

    def _get_locations(self, locations, application):
        """Build a dictionary of Location's from the locations module."""
        locations_map = {}
        for candidate_name in dir(locations):
            candidate = getattr(locations, candidate_name)
            if type(candidate) == type(locations.Location) and \
                   issubclass(candidate, locations.Location) and \
                   candidate != locations.Location:
                locations_map[candidate.path] = candidate(application)
                logger.info("Found %s class to handle path %s" % \
                            (candidate.__name__, candidate.path))
        return locations_map

    def start(self):
        logger.info("Starting server")
        next_maintenance = time.time()
        while True:
            rs, ws, es = select.select([self.httpd], [self.httpd], [], 1)
            if rs or ws:
                self.httpd.handle_request()
            if time.time() > next_maintenance:
                self.sessions.do_maintenance()
                next_maintenance = time.time() + 60 * config.Server.maintenance_period
               
