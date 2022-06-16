#!/usr/local/bin/python3
from gevent.pywsgi import WSGIServer
from server import APP, Cleaner

if __name__ == "__main__":
    Cleaner.runCleanerThread()
    http_server = WSGIServer(('', 60218), APP)
    http_server.serve_forever()