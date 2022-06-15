#!/usr/local/bin/python3

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

class YoutubeLegacy:
    @APP.route("/api/v1/getQualities", methods=["POST"])
    def getQualitiesV1():
        try:
            data = request.json
            if not data.get("url"):
                return "Please add an URL to your request"

            formatType = str(data.get("formatType")).lower()
            #none = default (full dict)

            url = data["url"]

            bestQualities = []

            _spaces = (60-len(f"Best quality _ for 123456"))*" "

            if "reddit.com" in url:
                bestQualities.append("Best quality 2 for Reddit" + _spaces + "[ID:bestvideo]")
                bestQualities.append("Best quality 1 for Reddit" + _spaces + "[ID:bestvideo+bestaudio]")
            elif "twitter.com" in url:
                bestQualities.append("Best quality for Twitter" + _spaces + "[ID:best]")
            elif "youtube.com" in url or "youtu.be" in url:
                bestQualities.append("Best audio quality for Youtube" + _spaces + "[ID:bestaudio]")
                bestQualities.append("Best video quality for Youtube" + _spaces + "[ID:bestvideo+bestaudio]")



            with ytdl.YoutubeDL({}) as ydl:
                meta = ydl.extract_info(url, download=False)
                _formats = meta.get('formats', [meta])
                formats = []
                
                if formatType == "ios":

                    formats.append("[ID:bestvideo]")
                    formats.append("[ID:best]")
                    formats.append("[ID:bestvideo+bestaudio]")
                    formats.append("[ID:bestaudio]")

                    for format in _formats:
                        res = str(format.get("resolution"))
                        id = " [ID:" + str(format.get("format_id")) + "]"
                        codecs = ""
                        fps = ""
                        filesize = ""
                        ext = ""

                        if format.get("fps"):
                            fps = " - " + str(format.get("fps")) + "fps"

                        if format.get("filesize"):
                            filesize = " (" + Utils.keep2DigitsAfterPeriod(int(format.get("filesize")) / 1000000) + "MB)"

                        if format.get("ext"):
                            ext = f" (" + format.get("ext") + ")"

                        spaces = (50-len(f"{res}{fps}{filesize}{ext}{id}"))*" " #60 seems reasonable

                        vcodec = str(format.get("vcodec"))
                        acodec = str(format.get("acodec"))
                        if vcodec != "none" and acodec != "none":
                            codecs = spaces + f"vcodec:{vcodec} | acodec:{acodec}"
                        elif vcodec != "none":
                            codecs = spaces + "vcodec:"+vcodec
                        elif acodec != "none":
                            codecs = spaces + "acodec:"+acodec

                        formats.append(f"{res}{fps}{filesize}{ext}{id}{codecs}")

                    for form in bestQualities:
                        formats.append(form)

                    formats = formats[::-1]
                
                else: #if format none
                    for format in _formats:
                        formats.append({
                            "res": format.get("resolution"),
                            "fps": format.get("fps"),
                            "filesize": format.get("filesize"),
                            "ext": format.get("ext"),
                            "acodec": format.get("acodec"),
                            "vcodec": format.get("vcodec"),
                            "id": format.get("format_id"),
                        })
                    
                    formats.append("[ID:bestvideo]")
                    formats.append("[ID:bestaudio]")
                    formats.append("[ID:bestvideo+bestaudio]")
                    formats.append("[ID:best]")

                    formats = formats[::-1]

                return {"formats": formats}
        except Exception:
            return traceback.format_exc()

    @APP.route("/api/v1/getVideo", methods=["GET"])
    def getVideoV1():
        try:
            data = request.headers
            format_id = data.get("id")
            url = data.get("url")

            if not url or not format_id:
                return "Please add an url or format id to your header requests"

            #convert = bool(data.get("convert")) USING WAY TOO MUCH CPU

            prefeeredFormat = data.get("prefFormat")
            if not prefeeredFormat:
                prefeeredFormat = "mp4"

            currentTime = time.time_ns()

            ydl_opts = {
                'outtmpl': f"videos/{currentTime}.%(ext)s",
                'format': format_id,
                'merge_output_format': prefeeredFormat,
                'ffmpeg_location': 'ffmpeg',
                "quiet": True
            }

            #handle audio 
            if prefeeredFormat in ["mp3", "m4a"] or format_id == "bestaudio":
                ydl_opts["format"] = "bestaudio[ext=m4a]/bestaudio[ext=mp3]"
                ydl_opts["audio_quality"] = 0
                ydl_opts["keepvideo"] = False

            with ytdl.YoutubeDL(ydl_opts) as ydl:
                ydl.download(url)

            print("Done getting file.")

            fileName = ""

            for file in os.listdir("videos/"):
                if str(currentTime) in file:
                    fileName = file

            return send_file(f"videos/{fileName}", download_name=f"{fileName}")
        
        except Exception:
            return traceback.format_exc()

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
                "format": "video"
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
    APP.run(host="0.0.0.0", port=12345)
