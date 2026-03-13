import os
import json
import argparse

from common import CTFPlatform
import requests
import re

class Zerosecone(CTFPlatform):
    def __init__(self, url, token):
        super().__init__("zerosecone", url, token)
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"{self.token}"})
        self.metadata = self.fetch_metadata()

    def fetch_metadata(self):
        # stage 1 fetch nuxt config
        resp = self.session.get(f"{self.url}/")
        try:
            nuxt_config = re.search(r"window\.__NUXT__\.config=(.*?)</script>", resp.text).group(1)
        except Exception:
            print("💥 Failed to fetch nuxt config")
            return {}
        try:
            code = re.search(r'code:"(.*?)"', nuxt_config).group(1)
        except Exception:
            print("💥 Failed to fetch code from nuxt config")
            return {}
        competition_id_resp = self.session.get(f"{self.url}/api/competitions/converter:code2id?code={code}")
        data = self.session.get(f"{self.url}/api/competitions/{competition_id_resp.json()['data']['id']}")
        metadata = {
            "id": data.json()['data']['id'],
            "title": data.json()['data']['title'],
            "status": data.json()['data']['status'],
            "start": data.json()['data']['game_start_at'],
            "end": data.json()['data']['game_end_at'],
        }
        return metadata

    def list_challenges(self):
        challenges = self.session.get(f"{self.url}/api/competitions/{self.metadata['id']}/challenges")
        if challenges.json()['code'] != 0:
            print(f"💥 Failed to fetch challenges: {challenges.json()['message']}")
            return []
        return challenges.json()['data']['challenges']
    
    def fetch_challenge(self, challenge_id):
        challenge = self.session.get(f"{self.url}/api/competitions/{self.metadata['id']}/challenges/{challenge_id}")
        return challenge.json()['data']
    
    def download_challenge_attachment(self, challenge_id):
        challenge = self.fetch_challenge(challenge_id)
        if challenge['attachment'] is None:
            print("💥 No attachment for this challenge")
            return None
        filename = challenge['attachment']['filename']
        if filename == "README":
            print("💥 No attachment for this challenge")
            return None
        size = challenge['attachment']['size']
        attachment = self.session.get(f"{self.url}/api/competitions/{self.metadata['id']}/challenges/{challenge_id}/attachments:download?token={self.token}")
        if not os.path.exists(f"attachments/{self.metadata['title']}"):
            os.makedirs(f"attachments/{self.metadata['title']}")
        with open(
            f"attachments/{self.metadata['title']}/{filename}", "wb"
        ) as f:
            f.write(attachment.content)
        print(f"✅ Attachment downloaded: {filename} ({size} bytes)")
        return filename
    
    def renew_instance(self, instance_id):
        instance = self.session.post(f"{self.url}/api/competitions/{self.metadata['id']}/instances/{instance_id}:renew")
        return instance.json()
    
    def stop_instance(self, instance_id):
        instance = self.session.post(f"{self.url}/api/competitions/{self.metadata['id']}/instances/{instance_id}:stop")
        return instance.json()
    
    def start_instance(self, challenge_id):
        instance = self.session.post(f"{self.url}/api/competitions/{self.metadata['id']}/challenges/{challenge_id}:run")
        return instance.json()
    

    def submit_flag(self, challenge_id, flag):
        submission = self.session.post(f"{self.url}/api/competitions/{self.metadata['id']}/challenges/{challenge_id}/flags:submit", json={"flag": flag})
        return submission.json()


def build_parser():
    parser = argparse.ArgumentParser(description="Zerosecone CTF API CLI")
    parser.add_argument("--url", "-u",  default=os.environ.get("ZEROSECONE_URL"), help="Platform base URL")
    parser.add_argument("--token", "-t",  default=os.environ.get("ZEROSECONE_TOKEN"), help="Auth token (or set ZEROSECONE_TOKEN)")

    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("metadata", help="Print competition metadata")
    subparsers.add_parser("list", help="List challenges")

    fetch_parser = subparsers.add_parser("fetch", help="Fetch one challenge by id")
    fetch_parser.add_argument("challenge_id", type=int)

    download_parser = subparsers.add_parser("download", help="Download challenge attachment")
    download_parser.add_argument("challenge_id", type=int)

    start_parser = subparsers.add_parser("start", help="Start challenge instance")
    start_parser.add_argument("challenge_id", type=int)

    stop_parser = subparsers.add_parser("stop", help="Stop instance by instance_id")
    stop_parser.add_argument("instance_id", type=int)

    renew_parser = subparsers.add_parser("renew", help="Renew instance by instance_id")
    renew_parser.add_argument("instance_id", type=int)

    submit_parser = subparsers.add_parser("submit", help="Submit flag")
    submit_parser.add_argument("challenge_id", type=int)
    submit_parser.add_argument("flag")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.url:
        parser.error("Missing URL. Pass --url or set ZEROSECONE_URL.")
    if not args.token:
        parser.error("Missing token. Pass --token or set ZEROSECONE_TOKEN.")

    platform = Zerosecone(args.url.rstrip("/"), args.token)

    if args.action == "metadata":
        result = platform.metadata
    elif args.action == "list":
        result = platform.list_challenges()
    elif args.action == "fetch":
        result = platform.fetch_challenge(args.challenge_id)
    elif args.action == "download":
        result = {"downloaded": platform.download_challenge_attachment(args.challenge_id)}
    elif args.action == "start":
        result = platform.start_instance(args.challenge_id)
    elif args.action == "stop":
        result = platform.stop_instance(args.instance_id)
    elif args.action == "renew":
        result = platform.renew_instance(args.instance_id)
    elif args.action == "submit":
        result = platform.submit_flag(args.challenge_id, args.flag)
    else:
        parser.error(f"Unsupported action: {args.action}")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()