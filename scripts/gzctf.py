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
        
        self.metadata = self.fetch_metadata()

    def fetch_metadata(self):
        resp = self.session.get(f"{self.url}")
        if resp.status_code != 200:
            print(f"💥 Failed to fetch game metadata: {resp.status_code} {resp.text}")
            return {}
        data = resp.json()
        metadata = {
            "id": data['id'],
            "title": data['title'],
            "status": data['status'],
            "start": data['start'],
            "end": data['end'],
        }
        return metadata
    
    def list_challenges(self):
        challenges = self.session.get(f"{self.url}/details")
        if challenges.status_code != 200:
            print(f"💥 Failed to fetch challenges: {challenges.status_code} {challenges.text}")
            return []
        return challenges.json()['challenges']
    
    def fetch_challenge(self, challenge_id):
        challenge = self.session.get(f"{self.url}/challenges/{challenge_id}")
        if challenge.status_code != 200:
            print(f"💥 Failed to fetch challenge {challenge_id}: {challenge.status_code} {challenge.text}")
            return {}
        return challenge.json()

    def download_challenge_attachment(self, challenge_id):
        challenge = self.fetch_challenge(challenge_id)
        if challenge == {}:
            print("💥 Challenge not found, cannot download attachment")
            return None
        if challenge["context"]["url"] is None:
            print("💥 No attachment for this challenge")
            return None
        title = self.metadata['title']
        url = challenge["context"]["url"]
        if url.startswith("assets/"):
            filename = f"{challenge['title']}_{url.split('/')[-1]}"
        else:
            filename = url.split("/")[-1] if url.split("/")[-1] != "" else f"{challenge['title']}_attachment"
        if url.startswith("/assets"):
            url = self.url.split("/api/game/")[0] + url
        else:
            print("⚠️ External attachment URL detected, maybe need manual download with browser: " + url)
        if not os.path.exists(f"attachments/{title}"):
            os.makedirs(f"attachments/{title}")
        attachment = self.session.get(url)
        with open(
            f"attachments/{title}/{filename}", "wb"
        ) as f:
            f.write(attachment.content)
        print(f"✅ Attachment downloaded: {filename} ({len(attachment.content)} bytes)")
        return filename
    
    def start_instance(self, challenge_id):
        # https://www.tpcup.org/api/game/1/container/20
        instance = self.session.post(f"{self.url}/container/{challenge_id}")
        if instance.status_code != 200:
            print(f"💥 Failed to start instance for challenge {challenge_id}: {instance.status_code} {instance.json()}")
            return {}
        data = instance.json()
        if len(data["entry"]) == 36 and ":" not in data["entry"]:
            data['entry'] = f"{self.url.split('/api/game/')[0].replace('http', 'ws')}/api/proxy/{data['entry']}, use WebSocat or WSRX to connect"
            print(f"⚠️ Instance started with WebSocket proxy mode: {data['entry']}")
        return data

    def renew_instance(self, instance_id):
        instance = self.session.post(f"{self.url}/container/{instance_id}/extend")
        if instance.status_code != 200:
            print(f"💥 Failed to renew instance {instance_id}: {instance.status_code} {instance.json()}")
            return {}
        data = instance.json()
        if len(data["entry"]) == 36 and ":" not in data["entry"]:
            data['entry'] = f"{self.url.split('/api/game/')[0].replace('http', 'ws')}/api/proxy/{data['entry']}, use WebSocat or WSRX to connect"
            print(f"⚠️ Instance started with WebSocket proxy mode: {data['entry']}")
        return data
    
    def stop_instance(self, instance_id):
        instance = self.session.delete(f"{self.url}/container/{instance_id}")
        if instance.status_code != 200:
            print(f"💥 Failed to stop instance {instance_id}: {instance.status_code} {instance.json()}")
            return {}
        return "Success"
    
    def submit_flag(self, challenge_id, flag):
        submission = self.session.post(f"{self.url}/challenges/{challenge_id}", json={"flag": flag})
        if submission.status_code != 200:
            print(f"💥 Failed to submit flag for challenge {challenge_id}: {submission.status_code} {submission.json()}")
            return {}
        submission_id = submission.json()
        result = self.session.get(f"{self.url}/challenges/{challenge_id}/status/{submission_id}")
        if result.status_code != 200:
            print(f"💥 Failed to get submission result for challenge {challenge_id}: {result.status_code} {result.json()}")
            return {}
        return result.json()

def build_parser():
    parser = argparse.ArgumentParser(description="GZCTF API CLI")
    parser.add_argument("--url", default=os.environ.get("GZCTF_URL"), help="Platform base URL (e.g. https://gzctf.com/api/game/1)")
    parser.add_argument("--token", default=os.environ.get("GZCTF_TOKEN"), help="Auth token (or set GZCTF_TOKEN)")

    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("metadata", help="Fetch game metadata")
    subparsers.add_parser("list", help="List all challenges")
    
    fetch_parser = subparsers.add_parser("fetch", help="Fetch challenge details")
    fetch_parser.add_argument("challenge_id", help="ID of the challenge to fetch")

    download_parser = subparsers.add_parser("download", help="Download challenge attachment")
    download_parser.add_argument("challenge_id", help="ID of the challenge to download attachment for")

    start_parser = subparsers.add_parser("start", help="Start a challenge instance")
    start_parser.add_argument("challenge_id", help="ID of the challenge to start instance for")

    renew_parser = subparsers.add_parser("renew", help="Renew a challenge instance")
    renew_parser.add_argument("instance_id", help="ID of the instance to renew")

    stop_parser = subparsers.add_parser("stop", help="Stop a challenge instance")
    stop_parser.add_argument("instance_id", help="ID of the instance to stop")

    submit_parser = subparsers.add_parser("submit", help="Submit a flag for a challenge")
    submit_parser.add_argument("challenge_id", help="ID of the challenge to submit flag for")
    submit_parser.add_argument("flag", help="Flag to submit")

    return parser.parse_args()

def main():
    args = build_parser()

    if not args.url:
        print("💥 Missing URL. Pass --url or set GZCTF_URL.")
        exit(1)
    if not args.token:
        print("💥 Missing token. Pass --token or set GZCTF_TOKEN.")
        exit(1)
    platform = GZCTF(args.url, args.token)
    if args.action == "metadata":
        result = platform.fetch_metadata()
    elif args.action == "list":
        result = platform.list_challenges()
    elif args.action == "fetch":
        result = platform.fetch_challenge(args.challenge_id)
    elif args.action == "download":
        result = platform.download_challenge_attachment(args.challenge_id)
    elif args.action == "start":
        result = platform.start_instance(args.challenge_id)
    elif args.action == "renew":
        result = platform.renew_instance(args.instance_id)
    elif args.action == "stop":
        result = platform.stop_instance(args.instance_id)
    elif args.action == "submit":
        result = platform.submit_flag(args.challenge_id, args.flag)

    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()