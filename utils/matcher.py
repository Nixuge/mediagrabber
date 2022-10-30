from urllib.parse import urlparse
import logging
import re

def get_valid_link(link: str) -> bool | str:
    # long function to determine if a link is valid
    # prefer to take out a bit of perfs at the cost of avoiding as much exploits as I can
    return Matcher(link).get_result_link()

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
                logging.debug(f"Matched {website} for URL {self.link}")
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
        
        logging.debug(f"Custom matched Youtube for URL {full} (from {self.link})")
        return full
    
    
    def _match_ph(self):
        #TODO
        return self.link
    
    def _match_odysee(self):
        #TODO
        return self.link