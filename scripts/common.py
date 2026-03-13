class CTFPlatform:
    def __init__(self, platform_type, url, token):
        self.platform_type = platform_type
        self.url = url
        self.token = token

    def fetch_metadata(self):
        pass

    def list_challenges(self):
        pass

    def fetch_challenge(self, challenge_id):
        pass

    def download_challenge_attachment(self, challenge_id):
        pass

    def submit_flag(self, challenge_id, flag):
        pass