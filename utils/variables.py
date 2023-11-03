import os
import logging
from flask import Flask


class Constants:
    CSV = f"v2.3.1" # Current Script version
    CAV = f"v2.3"  # Current API version
    VIDEOS_PATH = os.path.abspath('videos')


class Global:
    app = Flask(
        __name__,
        template_folder=os.path.abspath('web_files/html'),
        static_folder=os.path.abspath('web_files/static')
    )

    ytdl_logger = logging.getLogger("ytdl-ignore")
    ytdl_logger.disabled = True
