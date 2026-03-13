class CTFPlatform:
    def __init__(self, platform_type, url, token):
        self.platform_type = platform_type
        self.url = url
        self.token = token

    def fetch_metadata(self):
        print("💥 fetch_metadata not implemented for this platform")
        pass

    def list_challenges(self):
        print("💥 list_challenges not implemented for this platform")
        pass

    def fetch_challenge(self, challenge_id):
        print("💥 fetch_challenge not implemented for this platform")
        pass

    def download_challenge_attachment(self, challenge_id):
        print("💥 download_challenge_attachment not implemented for this platform")
        pass

    def start_instance(self):
        print("💥 start_instance not implemented for this platform")
        pass

    def stop_instance(self):
        print("💥 stop_instance not implemented for this platform")
        pass

    def renew_instance(self):
        print("💥 renew_instance not implemented for this platform")
        pass

    def submit_flag(self, challenge_id, flag):
        print("💥 submit_flag not implemented for this platform")
        pass