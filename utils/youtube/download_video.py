import time
import logging
import os
import yt_dlp as ytdl

from flask import send_file

from cleaning.cleaner import Cleaner
from cleaning.video import Video

from utils.variables import Global, Constants


def download_video(merge_output_format, format_id, url, extension_replace: str = ""):
    current_time = time.time_ns()
    Cleaner.addVideo(Video(current_time))

    ydl_opts = {
        # .mov needed or else apple doesn't recognize it as a video (thanks apple)
        "outtmpl": f"{Constants.VIDEOS_PATH}/{current_time}.%(ext)s",
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
    file_name: str
    for file in os.listdir(Constants.VIDEOS_PATH):
        if str(current_time) in file:
            file_name = file

    logging.debug(f"Final filename: {file_name}")

    # if audio return as m4a, else return as mov
    # TODO: remove dirty apple fix
    for f in formats:
        if f.get("format_id") == format_id and f.get("resolution") == "audio only":
            return send_file(f"{Constants.VIDEOS_PATH}/{file_name}", download_name=f"{file_name}")

    extension = file_name.split(".")[-1]

    download_name = file_name
    if extension_replace:
        download_name = file_name.replace(extension, extension_replace)

    return send_file(f"{Constants.VIDEOS_PATH}/{file_name}", download_name=f"{download_name}")
