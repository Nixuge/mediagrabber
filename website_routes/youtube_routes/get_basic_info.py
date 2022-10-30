import yt_dlp as ytdl
import logging

from flask import request
from datetime import timedelta

from utils.error_messages import ErrorMessages
from utils.variables import Global, Constants
from utils.matcher import get_valid_link


app = Global.app


@app.route(f"/api/{Constants.CAV}/get_basic_info")
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
