#!/bin/python3
import logging

from utils.logger import set_logger_levels
from utils.variables import Global
from cleaning.cleaner import Cleaner

import website_routes.flask_trickery
import website_routes.base_endpoints
import website_routes.api_endpoints

import website_routes.youtube_routes.get_all_qualities
import website_routes.youtube_routes.get_basic_info
import website_routes.youtube_routes.get_best_qualities
import website_routes.youtube_routes.get_video


# logger
set_logger_levels()
ytdl_logger = logging.getLogger("ytdl-ignore")
ytdl_logger.disabled = True


if __name__ == "__main__":
    Cleaner.runCleanerThread()
    Global.app.run(host="0.0.0.0", port=12345)
