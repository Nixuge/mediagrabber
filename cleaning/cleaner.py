import logging
import time
import threading
import os
from cleaning.video import Video

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