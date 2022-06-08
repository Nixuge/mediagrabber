#!/usr/local/bin/python3
from gevent.pywsgi import WSGIServer
from server import APP


if __name__ == "__main__":
    http_server = WSGIServer(('', 60218), APP)
    http_server.serve_forever()