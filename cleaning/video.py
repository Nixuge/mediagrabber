from dataclasses import dataclass
import time
from typing import Optional

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