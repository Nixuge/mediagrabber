#!/usr/local/bin/python3

from asyncio.log import logger
from dataclasses import dataclass
import threading
from typing import Optional
from flask import Flask, request, send_file, render_template, redirect, send_from_directory, wrappers
import yt_dlp as ytdl
import time
import os
import logging
import re
from datetime import timedelta
from urllib.parse import urlparse

app = Flask(__name__)
CAV = f"v2.2"  # Current API version

# LOGGING (for some reason logging.getLogger(__name__) doesn't work...)
logging.addLevelName(logging.DEBUG, "\033[1;36m%s\033[1;0m" % logging.getLevelName(
    logging.DEBUG))  # 37 = gray but blue good
logging.addLevelName(
    logging.INFO, "\033[1;36m%s\033[1;0m" % logging.getLevelName(logging.INFO))
logging.addLevelName(
    logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(
    logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

logger_format = "[%(levelname)s|%(filename)s:%(lineno)s@%(funcName)s] %(message)s"
logging.basicConfig(format=logger_format, level=logging.DEBUG)

# avoid yt-dlp output
ytdl_logger = logging.getLogger("ytdl-ignore")
ytdl_logger.disabled = True


class ErrorMessages:
    GENERIC = "An exception happened."
    NO_URL = "Please add an URL to your request. Refeer to <a href=\"/documentation\">this page</a> for more info about the endpoints."
    INVALID_URL = "Invalid URL. Refeer to <a href=\"/supported\">this page</a> for a list of supported websites."


class Matcher:
    domain_table = {
        "reddit": ["redd.it", "reddit.com", "reddit.fr"],
        "twitter": ["twitter.com", "twttr.com", "t.co", "twimg.com", "twitpic.com", "twitter.co", "twitter.fr"],
        "instagram": ["instagram.com", "instagram.fr"],
        "snapchat": ["snapchat.com"],
        "facebook": ["acebook.com","faacebook.com","facebbook.com","facebook.co","facebook.com","facebook.com.au","facebook.com.mx","facebook.it","facebook.net","fb.audio","fb.com","fb.gg","fb.me","fb.watch","fbcdn.net","internet.org"],
    }

    def __init__(self, to_match):
        parsed_url = urlparse(to_match)
        self.link = to_match
        self.hostname = parsed_url.netloc
        self.domain = '.'.join(self.hostname.split('.')[-2:])
        self.custom_matchers = [
            self._custom_match_youtube,
        ]

    def get_result_link(self) -> bool | str:
        for custom_matcher in self.custom_matchers:
            result = custom_matcher()
            if result: return result

        for website, domains in self.domain_table:
            if self.domain in domains:
                logger.debug(f"Matched {website} for URL {self.link}")
                return self.link

        return False

    def _custom_match_youtube(self):
        # https://stackoverflow.com/a/37704433
        regex = "^((?:https?:)?\/\/)?((?:music|www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"

        match = re.fullmatch(regex, self.link)
        if not match: 
            return False

        full = ""
        for group in match.groups():
            if not group or group[:5] in ["&list", "?list"]: continue
            full += group
        
        logger.debug(f"Custom matched Youtube for URL {full} (from {self.link})")
        return full
    
    
    def _match_ph(self):
        #TODO
        return self.link
    
    def _match_odysee(self):
        #TODO
        return self.link


class Utils:
    @staticmethod
    def keep2DigitsAfterPeriod(i) -> str:
        i = str(i)
        split = i.split(".")
        return split[0] + "." + split[1][:2]

    @staticmethod
    def getFormats(formats):
        HAS_AUDIO_FORMAT = False
        HAS_VIDEO_FORMAT = False
        for f in formats:
            resolution = f.get("resolution")
            if resolution != None:
                if resolution == "audio only":
                    HAS_AUDIO_FORMAT = True
                if "x" in resolution:
                    HAS_VIDEO_FORMAT = True

        IS_GENERIC = not HAS_AUDIO_FORMAT and not HAS_VIDEO_FORMAT
        return HAS_AUDIO_FORMAT, HAS_VIDEO_FORMAT, IS_GENERIC

    @staticmethod
    def get_valid_link(link: str) -> bool | str:
        # long function to determine if a link is valid
        # prefer to take out a bit of perfs at the cost of avoiding as much exploits as I can
        return Matcher(link).get_result_link()


class Website:
    @app.route('/api/', defaults={'path': ''})
    @app.route('/api/<path:path>')
    def catch_all_api(path):
        return f"Invalid API path. Please make sure your API version is set correctly ({CAV}). Otherwise, see the documentation @ mediagrabber.nixuge.me/ (URL requested: /api/{path})"

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return redirect("https://mediagrabber.nixuge.me", code=302)

    @app.route("/index")
    @app.route("/index.html")
    @app.route("/")
    def index():
        return render_template("index.html", current_api_version=CAV)

    @app.route("/doc")
    @app.route("/doc.html")
    @app.route("/documentation")
    @app.route("/documentation.html")
    def doc():
        return render_template("doc.html")

    @app.route("/supported")
    @app.route("/supported.html")
    def supported():
        return render_template("supported.html")


class Global:
    @app.after_request
    def add_header(response: wrappers.Response):
        # only cache static files (js/css)
        # otherwise chrome doesn't like it.
        # max-age = 1 day (60*60*24)
        ct = response.content_type
        if "javascript" in ct or "css" in ct:
            response.headers['Cache-Control'] = 'public, max-age=86400'

        return response

    @app.route("/api/get_current_version")
    @app.route("/api/get_api_version")
    def get_current_version():
        return CAV

    @app.route("/static/<path:path>")
    def get_static_content(path):
        return send_from_directory("static", path)


@dataclass
class Video:
    name: str  # name WITHOUT EXTENSION
    expiration_date: int

    def __init__(self, name: str, expiration_date: Optional[int] = None) -> None:
        if expiration_date == None:
            # set expiration date 240s in the future
            expiration_date = (time.time_ns() + 240000000000)
            # expiration_date = (time.time_ns() + 120000000000) #set expiration date 120s in the future

        self.name = str(name)
        self.expiration_date = expiration_date

# honestly not the fanciest
# but wanted to keep it in 1 class and does the job :D


class Cleaner:
    videos_path = "videos"
    _toClean: list[Video] = []
    _thread: threading.Thread = None

    @staticmethod
    def addVideo(video: Video) -> None:
        if type(video) != Video:
            return
        Cleaner._toClean.append(video)
        logging.debug(f"Added video to clean: {video}")

    @staticmethod
    def runCleanerThread() -> None:
        if Cleaner._thread != None:
            logging.warning("Cleaner already running")
            return

        Cleaner._thread = threading.Thread(target=Cleaner.threadFunc)
        Cleaner._thread.start()

    @staticmethod
    def threadFunc() -> None:  # could make it as a diff class but honestly no need
        logging.info("Cleaner thread started")
        while True:
            current_time = time.time_ns()

            for video in Cleaner._toClean:
                if video.expiration_date < current_time:  # detection & clear from the list
                    Cleaner._toClean.remove(video)

                    deleted_files: int = 0
                    # clear the actual video file
                    for file in os.listdir(f"{Cleaner.videos_path}/"):
                        if video.name in file:
                            deleted_files += 1
                            os.remove(f"{Cleaner.videos_path}/{file}")

                    logging.debug(
                        f"Video expired: {video.name} | Removed {deleted_files} files")

            # ok stopping the thread since it's running along the main one
            time.sleep(1)


class Youtube:
    @app.route(f"/api/{CAV}/get_basic_info")
    def get_basic_info():
        headers_data = request.headers
        url = headers_data.get("Requested-Url")
        if not url:
            logging.error("Needs an URL")
            return ErrorMessages.NO_URL, 400
        
        url = Utils.get_valid_link(url)
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
        
        url = Utils.get_valid_link(url)
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
        HAS_AUDIO_FORMAT, HAS_VIDEO_FORMAT, IS_GENERIC = Utils.getFormats(
            formats)
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

        url = Utils.get_valid_link(url)
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

    @staticmethod
    def _get_video(merge_output_format, format_id, url, force_to_format: str = "mov"):
        CURRENT_TIME = time.time_ns()
        Cleaner.addVideo(Video(CURRENT_TIME))

        ydl_opts = {
            # .mov needed or else apple doesn't recognize it as a video (thanks apple)
            "outtmpl": f"videos/{CURRENT_TIME}.%(ext)s",
            "merge_output_format": merge_output_format,
            "ffmpeg_location": "/usr/bin/ffmpeg",
            "quiet": True,
            "logger": ytdl_logger
        }
        if format_id:
            ydl_opts["format"] = format_id

        logging.debug(f"Downloading video {url}")
        logging.debug(
            f"Output: {merge_output_format}, Force to: {force_to_format}, ID: {format_id}")

        # handle if audio format
        with ytdl.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url)
            formats = meta.get('formats', [meta])

        logging.debug(f"Done downloading {url}")

        # get the filemane in a dirty way since yt-dlp doesn't let us get it easily
        FILE_NAME: str
        for file in os.listdir("videos/"):
            if str(CURRENT_TIME) in file:
                FILE_NAME = file

        logging.debug(f"Final filename: {FILE_NAME}")

        # if audio return as m4a, else return as mov
        for f in formats:
            if f.get("format_id") == format_id and f.get("resolution") == "audio only":
                return send_file(f"videos/{FILE_NAME}", download_name=f"{FILE_NAME}")

        EXTENSION = FILE_NAME.split(".")[-1]

        # dirty fix since apple doesn't want to save anything except .movs (& gifs) even if the codecs work
        if force_to_format and not EXTENSION in ["gif"] and merge_output_format != "mkv":
            DOWNLOAD_NAME = FILE_NAME.replace(EXTENSION, force_to_format)
            return send_file(f"videos/{FILE_NAME}", download_name=f"{DOWNLOAD_NAME}")

        return send_file(f"videos/{FILE_NAME}", download_name=f"{FILE_NAME}")

    @app.route(f"/api/{CAV}/get_video")
    def get_video():
        data = request.headers
        format_id = data.get("Id")

        url = data.get("Requested-Url")
        if not url:
            logging.error("Needs an URL")
            return ErrorMessages.NO_URL, 400

        url = Utils.get_valid_link(url)
        if not url:
            logging.error(f"Invalid URL: {url}")
            return ErrorMessages.INVALID_URL, 400

        format_extension = data.get("Format-Extension")
        if not format_extension:
            format_extension = "mov"

        # setup that way so that by default it retries as a mkv (which supports pretty much everything)
        dont_retry_as_mkv = data.get("Dont_Retry_As_Mkv")

        try:
            return Youtube._get_video(format_extension, format_id, url)
        except Exception as e:
            logging.warning(f"Failed as a {format_extension} ({e})")
            if dont_retry_as_mkv:
                return f"{e}", 400
            else:
                logging.debug("Retrying as mkv")
                try:
                    return Youtube._get_video("mkv", format_id, url)
                except Exception as e:
                    return f"Exception happened! {e}", 400


if __name__ == "__main__":
    Cleaner.runCleanerThread()
    app.run(host="0.0.0.0", port=12345)
