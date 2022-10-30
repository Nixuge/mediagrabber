import yt_dlp as ytdl
import logging

from flask import request

from utils.error_messages import ErrorMessages
from utils.variables import Global, Constants
from utils.matcher import get_valid_link


app = Global.app


@app.route(f"/api/{Constants.CAV}/get_all_qualities")
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

    with ytdl.YoutubeDL({"quiet": True, "logger": Global.ytdl_logger}) as ydl:
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
