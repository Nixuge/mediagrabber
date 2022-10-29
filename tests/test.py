import yt_dlp as ytdl
import json

with ytdl.YoutubeDL({"quiet": True}) as ydl:
    meta = ydl.extract_info("url", download=False)
    # formats = meta.get('formats', [meta])
    # with open("ccreddit.json", "w") as openfile:
        # json.dump(meta, openfile, indent=4)
    print(meta.get('thumbnail'))
    print(meta.get('title'))
    print(meta.get("uploader"))
    print(meta.get("extractor_key"))
    print(meta.get("duration"))