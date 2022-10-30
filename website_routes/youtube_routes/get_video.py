import logging

from flask import request

from utils.error_messages import ErrorMessages
from utils.variables import Global, Constants
from utils.matcher import get_valid_link

from utils.youtube.download_video import download_video


app = Global.app


@app.route(f"/api/{Constants.CAV}/get_video")
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
