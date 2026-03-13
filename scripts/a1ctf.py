import os
import json
import argparse
import time

from common import CTFPlatform
import requests
import re

class A1CTF(CTFPlatform):
    def __init__(self, url, token):
        super().__init__("a1ctf", url, token)
        self.session = requests.Session()
        self.session.cookies.update({"a1token": self.token})
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
        data = resp.json()['data']
        metadata = {
            "id": data['game_id'],
            "title": data['name'],
            "start": data['start_time'],
            "end": data['end_time'],
        }
        return metadata
    
    def list_challenges(self):
        challenges = self.session.get(f"{self.url}/challenges")
        if challenges.status_code != 200:
            print(f"💥 Failed to fetch challenges: {challenges.status_code} {challenges.text}")
            return []
        return challenges.json()['data']['challenges']
    
    def fetch_challenge(self, challenge_id):
        challenge = self.session.get(f"{self.url}/challenge/{challenge_id}")
        if challenge.status_code != 200:
            print(f"💥 Failed to fetch challenge {challenge_id}: {challenge.status_code} {challenge.text}")
            return {}
        return challenge.json()['data']
    
    def download_challenge_attachment(self, challenge_id):
        challenge = self.fetch_challenge(challenge_id)
        if challenge == {}:
            print("💥 Challenge not found, cannot download attachment")
            return None
        if challenge["attachments"] == []:
            print("💥 No attachment for this challenge")
            return None
        if not os.path.exists(f"attachments/{self.metadata['title']}/{challenge['challenge_name']}"):
            os.makedirs(f"attachments/{self.metadata['title']}/{challenge['challenge_name']}")
        for attachment in challenge["attachments"]:
            if attachment["attach_type"] == "STATICFILE":
                url = f"{self.url.split('/api')[0]}/api/file/download/{attachment['attach_hash']}"
            else:
                url = attachment["attach_url"]
            filename = attachment["attach_name"]
            filepath = f"attachments/{self.metadata['title']}/{challenge['challenge_name']}/{filename}"
            attachment_data = self.session.get(url)
            with open(filepath, "wb") as f:
                f.write(attachment_data.content)
            print(f"✅ Downloaded attachment to {filepath}")

    def start_instance(self, challenge_id):
        instance = self.session.post(f"{self.url}/container/{challenge_id}")
        if instance.status_code != 200:
            print(f"💥 Failed to start instance for challenge {challenge_id}: {instance.status_code} {instance.json()}")
            return {}
        data = instance.json()
        if data["code"] != 200:
            print(f"💥 Failed to start instance for challenge {challenge_id}: {data['message']}")
        time.sleep(1)
        for i in range(10):
            instance_status = self.session.get(f"{self.url}/container/{challenge_id}")
            if instance_status.status_code != 200:
                print(f"💥 Failed to get instance status for challenge {challenge_id}: {instance_status.status_code} {instance_status.json()}")
                return {}
            instance_status = instance_status.json()
            if instance_status["data"]["container_status"] == "ContainerRunning":
                print(f"✅ Instance is running")
                return instance_status['data']
            time.sleep(1)
        return data
    
    def renew_instance(self, instance_id):
        instance = self.session.patch(f"{self.url}/container/{instance_id}")
        if instance.status_code != 200:
            print(f"💥 Failed to renew instance {instance_id}: {instance.status_code} {instance.json()}")
            return {}
        data = instance.json()
        if data["code"] != 200:
            print(f"💥 Failed to renew instance {instance_id}: {data['message']}")
        return data

    def stop_instance(self, instance_id):
        instance = self.session.delete(f"{self.url}/container/{instance_id}")
        if instance.status_code != 200:
            print(f"💥 Failed to stop instance {instance_id}: {instance.status_code} {instance.json()}")
            return {}
        data = instance.json()
        if data["code"] != 200:
            print(f"💥 Failed to stop instance {instance_id}: {data['message']}")
        return data
    
    
    def submit_flag(self, challenge_id, flag):
        submission = self.session.post(f"{self.url}/flag/{challenge_id}", json={"flag": flag})
        if submission.status_code != 200:
            print(f"💥 Failed to submit flag for challenge {challenge_id}: {submission.status_code} {submission.json()}")
            return {}
        judge_id = submission.json()["data"]["judge_id"]
        result = self.session.get(f"{self.url}/flag/{judge_id}")
        if result.status_code != 200:
            print(f"💥 Failed to get submission result for challenge {challenge_id}: {result.status_code} {result.json()}")
            return {}
        return result.json()
    

def build_parser():
    parser = argparse.ArgumentParser(description="A1CTF Platform Interaction Script")
    parser.add_argument("--url", "-u",  default=os.getenv("A1CTF_URL"), help="Base URL of the target A1CTF platform (can also be set via A1CTF_URL env variable)")
    parser.add_argument("--token", "-t",  default=os.getenv("A1CTF_TOKEN"), help="Authentication token for A1CTF platform (can also be set via A1CTF_TOKEN env variable)")
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
        print("💥 Missing URL. Pass --url or set A1CTF_URL.")
        exit(1)
    if not args.token:
        print("💥 Missing token. Pass --token or set A1CTF_TOKEN.")
        exit(1)
    platform = A1CTF(args.url.rstrip("/"), args.token)
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