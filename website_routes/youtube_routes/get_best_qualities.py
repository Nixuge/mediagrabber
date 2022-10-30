import yt_dlp as ytdl
import logging

from flask import request

from utils.error_messages import ErrorMessages
from utils.variables import Global, Constants
from utils.global_utils import GlobalUtils
from utils.matcher import get_valid_link


app = Global.app


@app.route(f"/api/{Constants.CAV}/get_best_qualities")
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

    with ytdl.YoutubeDL({"quiet": True, "logger": Global.ytdl_logger}) as ydl:
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
