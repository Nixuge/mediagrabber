#!/usr/local/bin/python3
from gevent.pywsgi import WSGIServer
from server import app, Cleaner

if __name__ == "__main__":
    Cleaner.runCleanerThread()
    http_server = WSGIServer(('', 60218), app)
    http_server.serve_forever()