import os
import json
import argparse
import time

from common import CTFPlatform
import requests
import re

class Adworld(CTFPlatform):
    def __init__(self, url, token):
        super().__init__("adworld", url, token)
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"JWT {self.token}"})
        try:
            resource_id = re.search(r"/contest/flag/([^/]+)/", self.url).group(1)
        except:
            print("💥 Invalid URL format. Expected https://adworld.xctf.org.cn/page/mg/...")
            exit(1)
        self.url = f"https://adworld.xctf.org.cn/api/ct/web/jeopardy_race/race/{resource_id}/"
        self.metadata = self.fetch_metadata()

    def fetch_metadata(self):
        resp = self.session.get(f"{self.url}/base")
        if resp.status_code != 200:
            print(f"💥 Failed to fetch game metadata: {resp.status_code} {resp.text}")
            return {}
        if resp.json()['code'] != "AD-000000":
            print(f"💥 Failed to fetch game metadata: {resp.json()['message']}")
            return {}
        data = resp.json()['data']
        metadata = {
            "id": data['resource_id'],
            "title": data['race_name'],
            "start": data['start_time'],
            "end": data['end_time'],
        }
        return metadata
    
    def list_challenges(self):
        challenges = self.session.get(f"{self.url}/checkpoints/")
        if challenges.status_code != 200:
            print(f"💥 Failed to fetch challenges: {challenges.status_code} {challenges.text}")
            return []
        if challenges.json()['code'] != "AD-000000":
            print(f"💥 Failed to fetch challenges: {challenges.json()['message']}")
            return []
        return challenges.json()['data']['list']
    
    def fetch_challenge(self, challenge_id):
        challenge = self.session.get(f"{self.url}/checkpoints/{challenge_id}/")
        if challenge.status_code != 200:
            print(f"💥 Failed to fetch challenge {challenge_id}: {challenge.status_code} {challenge.text}")
            return {}
        if challenge.json()['code'] != "AD-000000":
            print(f"💥 Failed to fetch challenge {challenge_id}: {challenge.json()['message']}")
            return {}
        return challenge.json()['data']
    
    def download_challenge_attachment(self, challenge_id):
        challenge = self.fetch_challenge(challenge_id)
        if challenge == {}:
            print("💥 Challenge not found, cannot download attachment")
            return None
        if challenge["attachment"] == {}:
            print("💥 No attachment for this challenge")
            return None
        filename = challenge['attachment']['name']
        url = "https://adworld.xctf.org.cn" + challenge['attachment']['url']
        if not os.path.exists(f"attachments/{self.metadata['title']}/{challenge['name']}"):
            os.makedirs(f"attachments/{self.metadata['title']}/{challenge['name']}")
        filepath = f"attachments/{self.metadata['title']}/{challenge['name']}/{filename}"
        attachment = self.session.get(url)
        with open(filepath, "wb") as f:
            f.write(attachment.content)
        print(f"✅ Downloaded attachment to {filepath}")
        return filepath

    def start_instance(self, challenge_id):
        challenge = self.fetch_challenge(challenge_id)
        reference_type = challenge['scene_config']['reference_type']
        instance = self.session.post(f"{self.url}/scenes/", json={"checkpoint_id": challenge_id})
        if instance.status_code != 201:
            print(f"💥 Failed to start instance for challenge {challenge_id}: {instance.status_code} {instance.text}")
            return {}
        data = instance.json()
        if data["code"] != "AD-000000":
            print(f"💥 Failed to start instance for challenge {challenge_id}: {data['message']}")
            return {}
        for i in range(10):
            instance_status = self.session.get(f"{self.url}/scenes/dynamic/{challenge_id}/?reference={reference_type}")
            if instance_status.status_code != 200:
                print(f"💥 Failed to get instance status for challenge {challenge_id}: {instance_status.status_code} {instance_status.text}")
                return {}
            instance_status = instance_status.json()
            if instance_status["data"]["scene_status"] == 1:
                print(f"✅ Instance is running")
                return instance_status['data']
            time.sleep(1)
        return data['data']
    
    def submit_flag(self, challenge_id, flag):
        submission = self.session.post(f"{self.url}/flag/", json={"flag": flag, "checkpoint_id": challenge_id})
        if submission.status_code != 200:
            print(f"💥 Failed to submit flag for challenge {challenge_id}: {submission.status_code} {submission.text}")
            return {}
        if submission.json()['code'] != "AD-000000":
            print(f"💥 Failed to submit flag for challenge {challenge_id}: {submission.json()['message']}")
            return {}
        return submission.json()['data']

def build_parser():
    parser = argparse.ArgumentParser(description="Adworld API CLI")
    parser.add_argument("--url", "-u", default=os.getenv("ADWORLD_URL"), help="Base URL of the target Adworld CTF platform (can also be set via ADWORLD_URL env variable)")
    parser.add_argument("--token", "-t",  default=os.getenv("ADWORLD_TOKEN"), help="Authentication token for Adworld platform (can also be set via ADWORLD_TOKEN env variable)")
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
        print("💥 Missing URL. Pass --url or set ADWORLD_URL.")
        exit(1)
    if not args.token:
        print("💥 Missing token. Pass --token or set ADWORLD_TOKEN.")
        exit(1)
    platform = Adworld(args.url.rstrip("/"), args.token)
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
