#!/usr/local/bin/python3

from dataclasses import dataclass
import threading
from typing import Optional
from flask import Flask, request, send_file, render_template, redirect
import yt_dlp as ytdl
import time
import os
import logging

app = Flask(__name__)
CAV = f"v2.1" #Current API version
CURRENT_SCRIPT_VERSION = "2.1"

# LOGGING (for some reason logging.getLogger(__name__) doesn't work...)
logging.addLevelName(logging.DEBUG, "\033[1;36m%s\033[1;0m" % logging.getLevelName(logging.DEBUG)) #37 = gray but blue good
logging.addLevelName(logging.INFO, "\033[1;36m%s\033[1;0m" % logging.getLevelName(logging.INFO))
logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

logger_format = "[%(levelname)s|%(filename)s:%(lineno)s@%(funcName)s] %(message)s"
logging.basicConfig(format=logger_format, level=logging.DEBUG)

#avoid yt-dlp output
ytdl_logger = logging.getLogger("ytdl-ignore")
ytdl_logger.disabled = True


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
                if resolution == "audio only": HAS_AUDIO_FORMAT = True
                if "x" in resolution: HAS_VIDEO_FORMAT = True
        
        IS_GENERIC = not HAS_AUDIO_FORMAT and not HAS_VIDEO_FORMAT
        return HAS_AUDIO_FORMAT, HAS_VIDEO_FORMAT, IS_GENERIC


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
        return render_template("index.html")

    @app.route("/doc")
    @app.route("/doc.html")
    @app.route("/documentation")
    @app.route("/documentation.html")
    def download():
        return render_template("doc.html")

class Global:
    @app.route("/api/get_current_version")
    def get_current_version():
        return CURRENT_SCRIPT_VERSION


@dataclass
class Video:
    name: str #name WITHOUT EXTENSION
    expiration_date: int

    def __init__(self, name: str, expiration_date: Optional[int] = None) -> None:
        if expiration_date == None:
            # expiration_date = (time.time_ns() + 120000000000) #set expiration date 120s in the future
            expiration_date = (time.time_ns() + 60000000000) #set expiration date 60s in the future
            # expiration_date = (time.time_ns() + 20000000000) #set expiration date 20s in the future
        
        if type(name) != str:
            name = str(name)

        self.name = name
        self.expiration_date = expiration_date

#honestly not the fanciest
#but wanted to keep it in 1 class and does the job :D
class Cleaner:
    videos_path = "videos"
    _toClean: list[Video] = []
    _thread: threading.Thread = None

    @staticmethod
    def addVideo(video: Video) -> None:
        if type(video) != Video: return
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
    def threadFunc() -> None: #could make it as a diff class but honestly no need
        logging.info("Cleaner thread started")
        while True:
            current_time = time.time_ns()

            for video in Cleaner._toClean:
                if video.expiration_date < current_time: #detection & clear from the list
                    Cleaner._toClean.remove(video)

                    deleted_files: int = 0
                    for file in os.listdir(f"{Cleaner.videos_path}/"): #clear the actual video file
                        if video.name in file:
                            deleted_files += 1
                            os.remove(f"{Cleaner.videos_path}/{file}")
                    
                    logging.debug(f"Video expired: {video.name} | Removed {deleted_files} files")

            time.sleep(1) #ok stopping the thread since it's running along the main one


class Youtube:
    @app.route(f"/api/{CAV}/get_best_qualities")
    def get_best_qualities():
        logging.debug("Getting best qualities")
        headers_data = request.headers
        # FORMAT_TYPE = str(headers_data.get("format_type"))
        # could implement, but this is mostly for ios tbh
        URL = headers_data.get("url")
        if not URL:
            logging.error("Needs an URL")
            return "Please add an URL yo your request."


        with ytdl.YoutubeDL({"quiet": True, "logger": ytdl_logger}) as ydl:
            meta = ydl.extract_info(URL, download=False)
            formats = meta.get('formats', [meta])
        
        #get info about the media
        HAS_AUDIO_FORMAT, HAS_VIDEO_FORMAT, IS_GENERIC = Utils.getFormats(formats)
        logging.debug(f"Has audio: {HAS_AUDIO_FORMAT} | Has video: {HAS_VIDEO_FORMAT}")

        #generate the final dict
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
        #add a thing to see all
        final_formats["See all formats"] = {
            "value": None,
            "other": True
        }
        logging.debug(f"Total formats: {len(final_formats)}")
        #make a readable dictionary
        return final_formats


    @app.route(f"/api/{CAV}/get_all_qualities")
    def get_all_qualities():
        headers_data = request.headers
        URL = headers_data.get("url")
        if not URL:
            logging.error("Needs an URL")
            return "Please add an URL yo your request."
        
        with ytdl.YoutubeDL({"quiet": True, "logger": ytdl_logger}) as ydl:
            meta = ydl.extract_info(URL, download=False)
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
            "outtmpl": f"videos/{CURRENT_TIME}.%(ext)s", #.mov needed or else apple doesn't recognize it as a video (thanks apple)
            "merge_output_format": merge_output_format,
            "ffmpeg_location": "/usr/bin/ffmpeg",
            "quiet": True,
            "logger": ytdl_logger
        }
        if format_id:
            ydl_opts["format"] = format_id

        logging.debug(f"Downloading video {url}")
        logging.debug(f"Output: {merge_output_format}, Force to: {force_to_format}, ID: {format_id}")

        #handle if audio format
        with ytdl.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url)
            formats = meta.get('formats', [meta])

        logging.debug(f"Done downloading {url}")

            #get the filemane in a dirty way since yt-dlp doesn't let us get it easily
        FILE_NAME: str
        for file in os.listdir("videos/"):
            if str(CURRENT_TIME) in file:
                FILE_NAME = file

        logging.debug(f"Final filename: {FILE_NAME}")
        
            
        #if audio return as m4a, else return as mov
        for f in formats:
            if f.get("format_id") == format_id and f.get("resolution") == "audio only":
                return send_file(f"videos/{FILE_NAME}", download_name=f"{FILE_NAME}")

        EXTENSION = FILE_NAME.split(".")[-1]

        #dirty fix since apple doesn't want to save anything except .movs (& gifs) even if the codecs work
        if force_to_format and not EXTENSION in ["gif"] and merge_output_format != "mkv":
            DOWNLOAD_NAME = FILE_NAME.replace(EXTENSION, force_to_format)
            return send_file(f"videos/{FILE_NAME}", download_name=f"{DOWNLOAD_NAME}")
        
        return send_file(f"videos/{FILE_NAME}", download_name=f"{FILE_NAME}")

    @app.route(f"/api/{CAV}/get_video")
    def get_video():
        data = request.headers
        format_id = data.get("id")

        url = data.get("url")
        if not url: 
            logging.error("Needs an URL")
            return "Please add an url to your request headers."
        
        format_extension = data.get("format_extension")
        if not format_extension: format_extension = "mov"

        #setup that way so that by default it retries as a mkv (which supports pretty much everything)
        dont_retry_as_mkv = data.get("dont_retry_as_mkv")
        

        try:
            return Youtube._get_video(format_extension , format_id, url)
        except Exception as e:
            logging.warning(f"Failed as a {format_extension} ({e})")
            if dont_retry_as_mkv:
                return str(e)
            else:
                logging.debug("Retrying as mkv")
                return Youtube._get_video("mkv", format_id, url)


if __name__ == "__main__":
    Cleaner.runCleanerThread()
    app.run(host="0.0.0.0", port=12345)
