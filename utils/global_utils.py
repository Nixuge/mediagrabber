class GlobalUtils:
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