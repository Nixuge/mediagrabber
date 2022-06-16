#!/usr/local/bin/python3

from dataclasses import dataclass
import threading
from flask import Flask, request, send_file, render_template, redirect
import yt_dlp as ytdl
import traceback
import time
import os

APP = Flask(__name__)
CAV = f"v2.1" #Current API version
CURRENT_SCRIPT_VERSION = "2.1"

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
    @APP.route('/api/', defaults={'path': ''})
    @APP.route('/api/<path:path>')
    def catch_all_api(path):
        return f"Invalid API path. Please make sure your API version is set correctly ({CAV}). Otherwise, see the documentation @ mediagrabber.nixuge.me/ (URL requested: /api/{path})"

    @APP.route('/', defaults={'path': ''})
    @APP.route('/<path:path>')
    def catch_all(path):
        return redirect("https://mediagrabber.nixuge.me", code=302)
    
    @APP.route("/index")
    @APP.route("/index.html")
    @APP.route("/")
    def index():
        return render_template("index.html")

class Global:
    @APP.route("/api/get_current_version")
    def get_current_version():
        return CURRENT_SCRIPT_VERSION



@dataclass
class Video:
    name: str #name WITHOUT EXTENSION
    expiration_date: int

    def __init__(self, name: str, expiration_date: int or None) -> None:
        if expiration_date == None:
            # expiration_date = (time.time_ns() + 120000000000) #set expiration date 120s in the future
            expiration_date = (time.time_ns() + 20000000000) #set expiration date 20s in the future
        
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
    _threadStop: bool = False

    @staticmethod
    def addVideo(video: Video) -> None:
        if type(video) != Video: return
        Cleaner._toClean.append(video)

    @staticmethod
    def runCleanerThread() -> None:
        if Cleaner._thread != None: return #Already running
        Cleaner._thread = threading.Thread(target=Cleaner.threadFunc)
        Cleaner._thread.start()


    @staticmethod
    def stopCleanerThread() -> None:
        if Cleaner._thread == None: return #Already stopped
        Cleaner._threadStop = True
        Cleaner._thread = None #don't think it's needed but clean up memory

    @staticmethod
    def threadFunc() -> None: #could make it as a diff class but honestly no need
        print("Cleaner thread started !")
        while True:
            current_time = time.time_ns()

            for video in Cleaner._toClean:
                if video.expiration_date < current_time: #detection & clear from the list
                    print(f"Video expired: {video.name}")
                    Cleaner._toClean.remove(video)

                    for file in os.listdir(f"{Cleaner.videos_path}/"): #clear the actual video file
                        if video.name in file:
                            print(f"Deleted video: {file}")
                            os.remove(f"{Cleaner.videos_path}/{file}")
                    
            time.sleep(1) #ok stopping the thread since it's running along the main one




class Youtube:
    @APP.route(f"/api/{CAV}/get_best_qualities")
    def get_best_qualities():
        headers_data = request.headers

        # FORMAT_TYPE = str(headers_data.get("format_type"))
        # could implement, but this is mostly for ios tbh
        URL = headers_data.get("url")
        if not URL:
            return "Please add an URL yo your request."


        with ytdl.YoutubeDL({}) as ydl:
            meta = ydl.extract_info(URL, download=False)
            formats = meta.get('formats', [meta])
        
        #get info about the media
        HAS_AUDIO_FORMAT, HAS_VIDEO_FORMAT, IS_GENERIC = Utils.getFormats(formats)


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

        #make a readable dictionary
        return final_formats


    @APP.route(f"/api/{CAV}/get_all_qualities")
    def get_all_qualities():
        headers_data = request.headers
        URL = headers_data.get("url")
        if not URL:
            return "Please add an URL yo your request."
        
        with ytdl.YoutubeDL({}) as ydl:
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
        
        return final_formats

    @staticmethod
    def _get_video(merge_output_format, format_id, url, force_to_format: str = "mov"):
        CURRENT_TIME = time.time_ns()
        Cleaner.addVideo(Video(CURRENT_TIME))

        ydl_opts = {
            'outtmpl': f"videos/{CURRENT_TIME}.%(ext)s", #.mov needed or else apple doesn't recognize it as a video (thanks apple)
            'merge_output_format': merge_output_format,
            'ffmpeg_location': '/usr/bin/ffmpeg',
            "quiet": True
        }
        if format_id:
            ydl_opts["format"] = format_id

        #handle if audio format
        with ytdl.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url)
            formats = meta.get('formats', [meta])

            #get the filemane in a dirty way since yt-dlp doesn't let us get it easily
        FILE_NAME: str
        for file in os.listdir("videos/"):
            if str(CURRENT_TIME) in file:
                FILE_NAME = file

            
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

    @APP.route(f"/api/{CAV}/get_video")
    def get_video():
        data = request.headers
        format_id = data.get("id")

        url = data.get("url")
        if not url: return "Please add an url or format id to your request headers."
        
        format_extension = data.get("format_extension ")
        if not format_extension: format_extension = "mov"

        #setup that way so that by default it retries as a mkv (which supports pretty much everything)
        dont_retry_as_mkv = data.get("dont_retry_as_mkv")
        
        try:
            return Youtube._get_video(format_extension , format_id, url)
        except Exception as e:
            if dont_retry_as_mkv:
                return str(e)
            else:
                print("TRYING AS MKV")
                return Youtube._get_video("mkv", format_id, url)


if __name__ == "__main__":
    Cleaner.runCleanerThread()
    APP.run(host="0.0.0.0", port=12345)
