import argparse
import json
import os
import glob
import requests
import math
from datetime import datetime

BASE_URL = "https://api.openalex.org/works"
CHUNK_SIZE = 50 # max size offered from openalex

def chunk_list(items, size):
    """Yield successive `size`-sized chunks from items."""
    for i in range(0, len(items), size):
        yield items[i:i + size]

def send_request(api_key, work_ids, output_file):
    """Send one request for a chunk of work_ids and write the response to output_file."""
    filter_value = "ids.openalex:" + "|".join(work_ids)

    params = {
        "per_page": 50,
        "filter": filter_value,
    }
    if api_key:
        params["api_key"] = api_key

    try:
        response = requests.get(BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        works = data["results"] # results array from openalex

        with open(output_file, "w", encoding="utf-8") as f:
            for work in works:
                f.write(json.dumps(work, ensure_ascii=False) + "\n")

        print(f"Results written to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def combine_jsonl_files(output_dir, combined_filename="output_combined.jsonl"):
    """Combine all request_*.json files in output_dir into a single jsonl file."""
    pattern = os.path.join(output_dir, "request_*.jsonl")
    files = sorted(
        glob.glob(pattern),
        key=lambda p: int(os.path.splitext(os.path.basename(p))[0].split("_")[1])
    )

    combined_path = os.path.join(output_dir, combined_filename)
    count = 0
    with open(combined_path, "w", encoding="utf-8") as outfile:
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as infile:
                for line in infile:
                    line = line.strip()
                    if line:
                        outfile.write(line + "\n")
                        count += 1

def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch OpenAlex works in chunks of 50 by work ID."
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="OpenAlex API key (or leave empty string if not needed).",
    )
    parser.add_argument(
        "--missing-work-ids",
        required=True,
        help="Path to the missing-work-ids.json file (keys are work IDs).",
    )
    return parser.parse_args()

def main():
    args = parse_args()

    with open(args.missing_work_ids, "r", encoding="utf-8") as f:
        missing_work_ids = json.load(f)

    api_key = args.api_key
    work_ids = list(missing_work_ids.keys())

    print(f"Requesting {len(work_ids)} in chunks of {CHUNK_SIZE} per request.")
    print(f"Resulting in {math.ceil(len(work_ids) / 50)} total requests:")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = f"outputs-{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    for i, chunk in enumerate(chunk_list(work_ids, CHUNK_SIZE), start=1):
        output_file = os.path.join(output_dir, f"request_{i}.jsonl")
        send_request(api_key, chunk, output_file)

    combine_jsonl_files(output_dir)
    print(f'Combined all request output files into output_combined.jsonl')

if __name__ == "__main__":
    main()

# python requester.py --api-key 7G2qHihsLzX7Jg6AvAyFIV --missing-work-ids ../crawler/outputs-2026-07-29_17-59-27/missing-work-ids.json