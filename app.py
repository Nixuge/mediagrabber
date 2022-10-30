#!/usr/local/bin/python3
from gevent.pywsgi import WSGIServer
import setup

from cleaning.cleaner import Cleaner
from utils.variables import Global

if __name__ == "__main__":
    Cleaner.runCleanerThread()
    http_server = WSGIServer(('', 60218), Global.app)
    http_server.serve_forever()