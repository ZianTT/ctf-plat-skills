import argparse
import requests


def build_parser():
    parser = argparse.ArgumentParser(description="CTF Platform Detection Script")
    parser.add_argument("--url", required=True, help="Base URL of the target CTF platform")
    return parser.parse_args()

def main():
    args = build_parser()
    url = args.url.rstrip("/")

    try:
        response = requests.get(url, timeout=5)
        if "ZEROSECONE" in response.content.decode():
            print("Detected: zerosecone")
        elif "GZCTF" in response.content.decode() or "::CTF" in response.content.decode():
            print("Detected: gzctf")
        else:
            print("💥 Unable to detect platform type from the provided URL.")
    except requests.RequestException as e:
        print(f"Error connecting to {url}: {e}")

if __name__ == "__main__":
    main()