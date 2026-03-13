import os
import json
import argparse

from common import CTFPlatform
import requests
import re

class GZCTF(CTFPlatform):
    def __init__(self, url, token):
        super().__init__("gzctf", url, token)
        self.session = requests.Session()
        self.session.cookies.update({"GZCTF_Token": self.token})
        # handle url to https://{domain}/api/game/{id} format
        if re.search(r"/games/\d+", self.url) or re.search(r"/api/game/\d+", self.url):
            game_id = re.search(r"/games/(\d+)", self.url).group(1) if re.search(r"/games/\d+", self.url) else re.search(r"/api/game/(\d+)", self.url).group(1)
            self.url = re.sub(r"(https?://[^/]+)/.*", r"\1/api/game/" + game_id, self.url)
        else:
            print("💥 Invalid URL format. Expected https://{domain}/api/game/{id} or https://{domain}/games/{id}")
            exit(1)
        
        # self.metadata = self.fetch_metadata()
