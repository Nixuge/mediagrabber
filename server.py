#!/usr/local/bin/python3

from flask import request, send_file, wrappers
import yt_dlp as ytdl
import time
import os
import logging
from datetime import timedelta

from utils.logger import set_logger_levels
from utils.error_messages import ErrorMessages
from utils.matcher import get_valid_link
from utils.global_utils import GlobalUtils

from cleaning.cleaner import Cleaner
from cleaning.video import Video

from utils.variables import Global, Constants

import website_routes.flask_trickery
import website_routes.base_endpoints
import website_routes.api_endpoints

from utils.youtube.download_video import download_video

# settings vars
template_dir = os.path.abspath('web_files/html')
static_url_dir = os.path.abspath('web_files/static')
app = Global.app
CAV = f"v2.2"  # Current API version

# logger
set_logger_levels()
ytdl_logger = logging.getLogger("ytdl-ignore")
ytdl_logger.disabled = True




class Youtube:
    @app.route(f"/api/{CAV}/get_basic_info")
    def get_basic_info():
        headers_data = request.headers
        url = headers_data.get("Requested-Url")
        if not url:
            logging.error("Needs an URL")
            return ErrorMessages.NO_URL, 400

        url = get_valid_link(url)
        if not url:
            logging.error(f"Invalid URL: {url}")
            return ErrorMessages.INVALID_URL, 400

        logging.debug("Getting basic info for URL")
        meta: dict
        with ytdl.YoutubeDL({"quiet": True}) as ydl:
            try:
                meta = ydl.extract_info(url, download=False)
            except Exception as e:
                return f"{ErrorMessages.GENERIC} {e}", 400

        friendly_dict = {}
        for key in ["thumbnail", "title", "uploader", "extractor_key"]:
            if key in meta:
                friendly_dict[key] = meta.get(key)

        if "duration" in meta:
            friendly_dict["duration"] = str(
                timedelta(seconds=meta.get("duration")))

        return friendly_dict

    @app.route(f"/api/{CAV}/get_best_qualities")
    def get_best_qualities():
        headers_data = request.headers
        # FORMAT_TYPE = str(headers_data.get("format_type"))
        # could implement, but this is mostly for ios tbh
        url = headers_data.get("Requested-Url")
        if not url:
            logging.error("Needs an URL")
            return ErrorMessages.NO_URL, 400

        url = get_valid_link(url)
        if not url:
            logging.error(f"Invalid URL: {url}")
            return ErrorMessages.INVALID_URL, 400

        logging.debug(f"Getting best qualities for URL {url}")

        with ytdl.YoutubeDL({"quiet": True, "logger": ytdl_logger}) as ydl:
            try:
                meta = ydl.extract_info(url, download=False)
            except Exception as e:
                return f"{ErrorMessages.GENERIC} {e}", 400

            formats = meta.get('formats', [meta])

        # get info about the media
        HAS_AUDIO_FORMAT, HAS_VIDEO_FORMAT, IS_GENERIC = \
            GlobalUtils.getFormats(formats)

        logging.debug(
            f"Has audio: {HAS_AUDIO_FORMAT} | Has video: {HAS_VIDEO_FORMAT}")

        # generate the final dict
        final_formats = {
            "Auto best value from yt-dlp (recommended)": {
                "value": "",
            }
        }
        if HAS_AUDIO_FORMAT and HAS_VIDEO_FORMAT:
            final_formats["Best video and best audio merged"] = {
                "value": "bestvideo+bestaudio",
            }
        if HAS_VIDEO_FORMAT:
            final_formats["Best video (only)"] = {
                "value": "bestvideo",
            }
        if HAS_AUDIO_FORMAT:
            final_formats["Best audio (only)"] = {
                "value": "bestaudio",
            }
        if IS_GENERIC:
            final_formats["Best single-file format (generic)"] = {
                "value": "best",
            }
        # add a thing to see all
        final_formats["See all formats"] = {
            "value": None,
            "other": True
        }
        logging.debug(f"Total formats: {len(final_formats)}")
        # make a readable dictionary
        return final_formats

    @app.route(f"/api/{CAV}/get_all_qualities")
    def get_all_qualities():
        headers_data = request.headers
        url = headers_data.get("Requested-Url")
        if not url:
            logging.error("Needs an URL")
            return ErrorMessages.NO_URL, 400

        url = get_valid_link(url)
        if not url:
            logging.error(f"Invalid URL: {url}")
            return ErrorMessages.INVALID_URL, 400

        logging.debug(f"Getting all qualities for URL {url}")

        with ytdl.YoutubeDL({"quiet": True, "logger": ytdl_logger}) as ydl:
            try:
                meta = ydl.extract_info(url, download=False)
            except Exception as e:
                return f"{ErrorMessages.GENERIC} {e}", 400
            formats = meta.get('formats', [meta])

        final_formats = {}

        for f in formats:
            key = f"{f.get('format_id')} (.{f.get('ext')}) {f.get('resolution')}"
            final_formats[key] = {
                "value": f.get('format_id')
            }

        final_formats["Choose custom value"] = {
            "value": "CUSTOM"
        }
        logging.debug(f"Total formats: {len(final_formats)}")
        return final_formats

    @app.route(f"/api/{CAV}/get_video")
    def get_video():
        data = request.headers
        format_id = data.get("Id")

        url = data.get("Requested-Url")
        if not url:
            logging.error("Needs an URL")
            return ErrorMessages.NO_URL, 400

        url = get_valid_link(url)
        if not url:
            logging.error(f"Invalid URL: {url}")
            return ErrorMessages.INVALID_URL, 400

        format_extension = data.get("Format-Extension")
        if not format_extension:
            format_extension = "mov"

        # setup that way so that by default it retries as a mkv (which supports pretty much everything)
        dont_retry_as_mkv = data.get("Dont_Retry_As_Mkv")

        try:
            return download_video(format_extension, format_id, url)
        except Exception as e:
            logging.warning(f"Failed as a {format_extension} ({e})")
            if dont_retry_as_mkv:
                return f"{e}", 400
            else:
                logging.debug("Retrying as mkv")
                try:
                    return download_video("mkv", format_id, url)
                except Exception as e:
                    return f"Exception happened! {e}", 400


if __name__ == "__main__":
    Cleaner.runCleanerThread()
    app.run(host="0.0.0.0", port=12345)
