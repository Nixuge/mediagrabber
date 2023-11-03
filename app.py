#!/bin/python3
from gevent.pywsgi import WSGIServer
from yt_dlp import version
import setup

from cleaning.cleaner import Cleaner
from utils.variables import Global

if __name__ == "__main__":
    Cleaner.runCleanerThread()
    print(f"Running yt-dlp version {version.__version__} (channel {version.CHANNEL}, head {version.RELEASE_GIT_HEAD})")
    http_server = WSGIServer(('', 60218), Global.app)
    http_server.serve_forever()