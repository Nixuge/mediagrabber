import time
import logging
import os
import yt_dlp as ytdl

from flask import send_file

from cleaning.cleaner import Cleaner
from cleaning.video import Video

from utils.variables import Global, Constants


def download_video(merge_output_format, format_id, url, extension_replace: str = ""):
    CURRENT_TIME = time.time_ns()
    Cleaner.addVideo(Video(CURRENT_TIME))

    ydl_opts = {
        # .mov needed or else apple doesn't recognize it as a video (thanks apple)
        "outtmpl": f"{Constants.VIDEOS_PATH}/{CURRENT_TIME}.%(ext)s",
        "merge_output_format": merge_output_format,
        "ffmpeg_location": "/usr/bin/ffmpeg",
        "quiet": True,
        "logger": Global.ytdl_logger
    }
    if format_id:
        ydl_opts["format"] = format_id

    logging.debug(f"Downloading video {url}")
    logging.debug(
        f"Output: {merge_output_format}, Extension replace: {extension_replace}, ID: {format_id}")

    # handle if audio format
    with ytdl.YoutubeDL(ydl_opts) as ydl:
        meta = ydl.extract_info(url)
        formats = meta.get('formats', [meta])

    logging.debug(f"Done downloading {url}")

    # get the filemane in a dirty way since yt-dlp doesn't let us get it easily
    FILE_NAME: str
    for file in os.listdir(Constants.VIDEOS_PATH):
        if str(CURRENT_TIME) in file:
            FILE_NAME = file

    logging.debug(f"Final filename: {FILE_NAME}")

    # if audio return as m4a, else return as mov
    for f in formats:
        if f.get("format_id") == format_id and f.get("resolution") == "audio only":
            return send_file(f"{Constants.VIDEOS_PATH}/{FILE_NAME}", download_name=f"{FILE_NAME}")

    EXTENSION = FILE_NAME.split(".")[-1]

    # dirty fix since apple doesn't want to save anything except .movs (& gifs) even if the codecs work
    if extension_replace and not EXTENSION in ["gif"] and merge_output_format != "mkv":
        DOWNLOAD_NAME = FILE_NAME.replace(EXTENSION, extension_replace)
        return send_file(f"{Constants.VIDEOS_PATH}/{FILE_NAME}", download_name=f"{DOWNLOAD_NAME}")

    return send_file(f"{Constants.VIDEOS_PATH}/{FILE_NAME}", download_name=f"{FILE_NAME}")